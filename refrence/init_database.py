#!/usr/bin/env python3

import os
import sys
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("init_database.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_init")

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
    
    # Parse connection string
    try:
        # Try standard format: postgresql://user:password@host:port/dbname
        if db_url.startswith("postgresql://"):
            conn = psycopg2.connect(db_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
        # Try key=value format
        else:
            params = {}
            for param in db_url.split():
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
            
            conn = psycopg2.connect(**params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def setup_vector_extension(conn):
    """Set up the pgvector extension if not already installed"""
    try:
        with conn.cursor() as cur:
            # Check if pgvector extension exists
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            if not cur.fetchone():
                logger.info("Installing pgvector extension...")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("pgvector extension installed successfully")
            else:
                logger.info("pgvector extension already installed")
        return True
    except Exception as e:
        logger.error(f"Failed to install pgvector extension: {e}")
        return False

def create_schema(conn):
    """Create the agent schema if it doesn't exist"""
    try:
        with conn.cursor() as cur:
            # Check if schema exists
            cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'agent'")
            if not cur.fetchone():
                logger.info("Creating agent schema...")
                cur.execute(sql.SQL("CREATE SCHEMA agent"))
                logger.info("Agent schema created successfully")
            else:
                logger.info("Agent schema already exists")
        return True
    except Exception as e:
        logger.error(f"Failed to create agent schema: {e}")
        return False

def create_tables(conn):
    """Create all necessary tables for the Prism-DB framework"""
    try:
        with conn.cursor() as cur:
            # Create prism_agent_knowledge table
            logger.info("Creating agent.prism_agent_knowledge table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent.prism_agent_knowledge (
                    id SERIAL PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    metadata JSONB DEFAULT '{}'::JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create prism_agent_metadata table
            logger.info("Creating agent.prism_agent_metadata table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent.prism_agent_metadata (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    config JSONB NOT NULL DEFAULT '{}'::JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create prism_agent_memory table
            logger.info("Creating agent.prism_agent_memory table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent.prism_agent_memory (
                    id SERIAL PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    importance FLOAT DEFAULT 0.5,
                    metadata JSONB DEFAULT '{}'::JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create prism_agent_conversations table
            logger.info("Creating agent.prism_agent_conversations table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent.prism_agent_conversations (
                    id SERIAL PRIMARY KEY,
                    conversation_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    agents JSONB NOT NULL DEFAULT '[]'::JSONB,
                    messages JSONB NOT NULL DEFAULT '[]'::JSONB,
                    metadata JSONB DEFAULT '{}'::JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create vector indexes
            logger.info("Creating vector indexes...")
            # Check if indexes exist before creating them
            cur.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE indexname = 'idx_prism_agent_knowledge_embedding'
            """)
            if not cur.fetchone():
                cur.execute("""
                    CREATE INDEX idx_prism_agent_knowledge_embedding 
                    ON agent.prism_agent_knowledge USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
                logger.info("Created index on agent.prism_agent_knowledge.embedding")
            
            cur.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE indexname = 'idx_prism_agent_memory_embedding'
            """)
            if not cur.fetchone():
                cur.execute("""
                    CREATE INDEX idx_prism_agent_memory_embedding 
                    ON agent.prism_agent_memory USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
                logger.info("Created index on agent.prism_agent_memory.embedding")
            
            # Create regular indexes
            logger.info("Creating regular indexes...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_prism_agent_knowledge_agent_id
                ON agent.prism_agent_knowledge (agent_id)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_prism_agent_memory_agent_id
                ON agent.prism_agent_memory (agent_id)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_prism_agent_memory_memory_type
                ON agent.prism_agent_memory (memory_type)
            """)
            
            logger.info("All tables and indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def main():
    """Main function to initialize the database"""
    logger.info("Starting database initialization...")
    
    # Load environment variables
    if not load_env():
        return 1
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        return 1
    
    try:
        # Set up pgvector extension
        if not setup_vector_extension(conn):
            return 1
        
        # Create schema
        if not create_schema(conn):
            return 1
        
        # Create tables
        if not create_tables(conn):
            return 1
        
        logger.info("Database initialization completed successfully")
        return 0
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main()) 