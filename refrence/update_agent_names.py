#!/usr/bin/env python3

import os
import sys
import json
import logging
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_agent_names.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("agent_name_updater")

def load_env():
    """Load environment variables from .env.agent file"""
    env_path = Path(__file__).parent / ".env.agent"
    if not env_path.exists():
        logger.error(f".env.agent file not found at {env_path}")
        return False
    
    load_dotenv(env_path)
    db_url = os.getenv("PRISM_DATABASE_URL")
    if not db_url:
        logger.error("PRISM_DATABASE_URL not found in .env.agent file")
        return False
    
    logger.info("Environment variables loaded successfully")
    return True

def get_db_connection():
    """Establish connection to the database"""
    db_url = os.getenv("PRISM_DATABASE_URL")
    
    try:
        # Try standard format: postgresql://user:password@host:port/dbname
        if db_url.startswith("postgresql://"):
            conn = psycopg2.connect(db_url)
            return conn
        # Try key=value format
        else:
            params = {}
            for param in db_url.split():
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
            
            conn = psycopg2.connect(**params)
            return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def normalize_agent_name(name):
    """
    Normalize agent name to comply with OpenAI function calling requirements:
    - Must contain only lowercase letters, numbers, and underscores
    - Must start with a letter
    - Must not end with an underscore
    - Must not contain consecutive underscores
    """
    # Convert to lowercase
    normalized = name.lower()
    
    # Replace spaces and special characters with underscores
    normalized = re.sub(r'[^a-z0-9]', '_', normalized)
    
    # Ensure it starts with a letter (prepend 'agent_' if needed)
    if not normalized[0].isalpha():
        normalized = f"agent_{normalized}"
    
    # Remove consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)
    
    # Remove trailing underscore
    normalized = normalized.rstrip('_')
    
    return normalized

def update_agent_config_files():
    """Update agent config files with normalized names"""
    agents_dir = Path(__file__).parent / "agents"
    if not agents_dir.exists():
        logger.error(f"Agents directory not found at {agents_dir}")
        return False
    
    updated_count = 0
    for config_file in agents_dir.glob("**/config.json"):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'name' in config:
                original_name = config['name']
                normalized_name = normalize_agent_name(original_name)
                
                if original_name != normalized_name:
                    logger.info(f"Updating agent name in {config_file}: {original_name} -> {normalized_name}")
                    config['name'] = normalized_name
                    config['original_name'] = original_name  # Keep original name for reference
                    
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    updated_count += 1
        except Exception as e:
            logger.error(f"Error updating {config_file}: {e}")
    
    logger.info(f"Updated {updated_count} agent config files")
    return True

def update_agents_in_database(conn):
    """Update agent names in the database tables"""
    try:
        # Get all agents from the database
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if the table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'agent' 
                    AND table_name = 'prism_agent_metadata'
                )
            """)
            
            if not cur.fetchone()['exists']:
                logger.warning("agent.prism_agent_metadata table does not exist yet, skipping database update")
                return True
            
            # Get all agents
            cur.execute("SELECT agent_id, name FROM agent.prism_agent_metadata")
            agents = cur.fetchall()
            
            if not agents:
                logger.info("No agents found in the database")
                return True
            
            # Update each agent with a normalized name
            updated_count = 0
            for agent in agents:
                original_name = agent['name']
                normalized_name = normalize_agent_name(original_name)
                
                if original_name != normalized_name:
                    logger.info(f"Updating agent in database: {original_name} -> {normalized_name}")
                    cur.execute("""
                        UPDATE agent.prism_agent_metadata
                        SET name = %s,
                            metadata = jsonb_set(
                                CASE WHEN metadata IS NULL THEN '{}'::jsonb ELSE metadata END,
                                '{original_name}',
                                %s::jsonb
                            )
                        WHERE agent_id = %s
                    """, (normalized_name, json.dumps(original_name), agent['agent_id']))
                    updated_count += 1
            
            conn.commit()
            logger.info(f"Updated {updated_count} agents in the database")
        return True
    except Exception as e:
        logger.error(f"Failed to update agents in database: {e}")
        conn.rollback()
        return False

def update_agent_py_files():
    """Update agent name references in Python files"""
    agents_dir = Path(__file__).parent / "agents"
    if not agents_dir.exists():
        logger.error(f"Agents directory not found at {agents_dir}")
        return False
    
    updated_count = 0
    for py_file in agents_dir.glob("**/*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Look for class definitions with "Agent" in the name
            agent_classes = re.findall(r'class\s+(\w+Agent)\s*\(', content)
            
            modified = False
            for class_name in agent_classes:
                # Check if we need to normalize this class name
                normalized_class_name = normalize_agent_name(class_name)
                
                if class_name != normalized_class_name and not normalized_class_name.endswith('agent'):
                    # Ensure it ends with 'agent' if it's an agent class
                    normalized_class_name += '_agent'
                
                if class_name != normalized_class_name:
                    logger.info(f"Updating agent class in {py_file}: {class_name} -> {normalized_class_name}")
                    # Replace the class definition
                    content = re.sub(
                        f'class\\s+{class_name}\\s*\\(',
                        f'class {normalized_class_name}(',
                        content
                    )
                    
                    # Replace references to the class
                    content = re.sub(
                        f'\\b{class_name}\\b',
                        normalized_class_name,
                        content
                    )
                    
                    modified = True
            
            if modified:
                with open(py_file, 'w') as f:
                    f.write(content)
                updated_count += 1
        except Exception as e:
            logger.error(f"Error updating {py_file}: {e}")
    
    logger.info(f"Updated {updated_count} Python files")
    return True

def main():
    """Main function to update agent names"""
    logger.info("Starting agent name update process...")
    
    # Load environment variables
    if not load_env():
        return 1
    
    # Update agent config files
    if not update_agent_config_files():
        logger.warning("Failed to update some agent config files")
    
    # Update agent Python files
    if not update_agent_py_files():
        logger.warning("Failed to update some agent Python files")
    
    # Connect to database and update agent names
    conn = get_db_connection()
    if conn:
        try:
            if not update_agents_in_database(conn):
                logger.warning("Failed to update some agents in database")
        finally:
            conn.close()
    
    logger.info("Agent name update process completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 