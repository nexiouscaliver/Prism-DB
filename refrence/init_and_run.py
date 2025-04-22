#!/usr/bin/env python3
"""
Initialize and run script for Prism-DB framework.
This script handles the initialization of the database tables and starts the services.
"""
import os
import logging
import subprocess
import time
import sys
import signal
import shutil
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prism_db_startup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("prism_startup")

# Global variables for process management
processes = {}

def signal_handler(sig, frame):
    """Handle termination signals to gracefully shut down all processes"""
    logger.info("Received termination signal. Shutting down all processes...")
    for name, process in processes.items():
        if process and process.poll() is None:
            logger.info(f"Terminating {name} process...")
            process.terminate()
            try:
                process.wait(timeout=5)
                logger.info(f"{name} process terminated successfully")
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} process did not terminate gracefully, killing...")
                process.kill()
    
    logger.info("All processes terminated. Exiting.")
    sys.exit(0)

def check_prerequisites():
    """Check if all prerequisites are met"""
    # Check if Python 3.9+ is installed
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        logger.error("Python 3.9 or higher is required")
        return False
    
    # Check if PostgreSQL is installed and running
    try:
        result = subprocess.run(
            ["pg_isready"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=True
        )
        logger.info("PostgreSQL server is running")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("PostgreSQL server is not running or not installed")
        return False
    
    return True

def check_env_files():
    """Check if necessary .env files exist and create them if they don't"""
    root_dir = Path(__file__).parent.absolute()
    
    # Check .env.agent file
    env_agent_path = root_dir / ".env.agent"
    if not env_agent_path.exists():
        logger.info(".env.agent file not found, creating a template...")
        with open(env_agent_path, "w") as f:
            f.write("""# OpenAI API key for the agents
OPENAI_API_KEY=
# Database connection string
PRISM_DATABASE_URL=postgresql://prismdb:prismdb@localhost:5432/agent
# Agent configuration
AGENT_MODEL=gpt-4-turbo
# Logging level
LOG_LEVEL=INFO
""")
        logger.warning(f"Created .env.agent template at {env_agent_path}. Please edit it with your own values.")
        return False
    
    # Verify .env.agent has required fields
    with open(env_agent_path, "r") as f:
        env_content = f.read()
        if "OPENAI_API_KEY=" in env_content and "=" in env_content.split("OPENAI_API_KEY=")[1].split("\n")[0]:
            logger.info("OPENAI_API_KEY is set in .env.agent")
        else:
            logger.error("OPENAI_API_KEY is not set in .env.agent")
            return False
    
    return True

def initialize_database():
    """Initialize the database schema and tables"""
    logger.info("Initializing database...")
    try:
        result = subprocess.run(
            [sys.executable, "init_database.py"],
            check=True,
            cwd=Path(__file__).parent.absolute()
        )
        logger.info("Database initialization completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def update_agent_names():
    """Update agent names to comply with OpenAI function calling requirements"""
    logger.info("Updating agent names in configuration files...")
    
    root_dir = Path(__file__).parent.absolute()
    
    # Update agent_config.json
    config_path = root_dir / "configs" / "agent_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Update agent names to valid format (alphanumeric and underscores only)
            for agent in config.get("agents", []):
                if "name" in agent:
                    # Replace spaces and special characters with underscores
                    old_name = agent["name"]
                    new_name = "".join(c if c.isalnum() else "_" for c in old_name)
                    
                    # Ensure it follows the pattern db_name_database_Postgres_Agent for DB agents
                    if "database" in old_name.lower() and "agent" in old_name.lower():
                        if not new_name.endswith("_Agent"):
                            new_name += "_Agent"
                        
                        # Add prefix if it's missing
                        if not new_name.startswith("db_"):
                            parts = new_name.split("_")
                            if "database" in parts and "Postgres" in parts:
                                db_name = parts[0] if parts[0] != "database" else "prism"
                                new_name = f"db_{db_name}_database_Postgres_Agent"
                    
                    agent["name"] = new_name
                    logger.info(f"Updated agent name from '{old_name}' to '{new_name}'")
                    
                    # Also update it in the instructions
                    if "instructions" in agent:
                        agent["instructions"] = agent["instructions"].replace(old_name, new_name)
            
            # Add dedicated Prism Database Agent if it doesn't exist
            has_prism_db_agent = any(
                agent.get("name") == "db_prism_database_Postgres_Agent" 
                for agent in config.get("agents", [])
            )
            
            if not has_prism_db_agent:
                prism_db_agent = {
                    "name": "db_prism_database_Postgres_Agent",
                    "description": "A dedicated agent for managing the Prism database schema and tables",
                    "instructions": """You are the db_prism_database_Postgres_Agent, responsible for managing the Prism database schema and tables.
Your primary role is to handle database operations, manage schema information, and provide access to the agent database.
You can run SQL queries, create tables, and manage database objects.
Always ensure data integrity and follow proper database practices.""",
                    "tools": ["postgres_query_tool"],
                    "model": "${AGENT_MODEL}"
                }
                config["agents"].append(prism_db_agent)
                logger.info("Added dedicated Prism Database Agent to the configuration")
            
            # Update team configuration to include the Prism Database Agent
            if "teams" in config:
                for team in config["teams"]:
                    if "members" in team and "db_prism_database_Postgres_Agent" not in team["members"]:
                        team["members"].append("db_prism_database_Postgres_Agent")
                        logger.info(f"Added Prism Database Agent to team '{team.get('name', 'unnamed')}'")
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("Updated agent configuration successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update agent names: {e}")
            return False
    else:
        logger.error(f"Agent configuration file not found at {config_path}")
        return False

def start_scheduler():
    """Start the scheduler process"""
    logger.info("Starting scheduler...")
    try:
        scheduler_process = subprocess.Popen(
            [sys.executable, "-m", "prism.scheduler"],
            cwd=Path(__file__).parent.absolute(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes["scheduler"] = scheduler_process
        logger.info(f"Scheduler started with PID {scheduler_process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        return False

def start_agent_server():
    """Start the agent server process"""
    logger.info("Starting agent server...")
    try:
        agent_server_process = subprocess.Popen(
            [sys.executable, "-m", "prism.server"],
            cwd=Path(__file__).parent.absolute(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes["agent_server"] = agent_server_process
        logger.info(f"Agent server started with PID {agent_server_process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start agent server: {e}")
        return False

def main():
    """Main function to initialize and run Prism-DB"""
    logger.info("Starting Prism-DB initialization and startup...")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Exiting.")
        return 1
    
    # Check and create necessary .env files
    if not check_env_files():
        logger.error("Environment files check failed. Please correct the issues and try again.")
        return 1
    
    # Update agent names in configuration
    if not update_agent_names():
        logger.error("Failed to update agent names. Exiting.")
        return 1
    
    # Initialize database schema and tables
    if not initialize_database():
        logger.error("Database initialization failed. Exiting.")
        return 1
    
    # Start scheduler
    if not start_scheduler():
        logger.error("Failed to start scheduler. Exiting.")
        return 1
    
    # Start agent server
    if not start_agent_server():
        logger.error("Failed to start agent server. Exiting.")
        # Make sure to terminate the scheduler if agent server fails to start
        if "scheduler" in processes and processes["scheduler"].poll() is None:
            processes["scheduler"].terminate()
        return 1
    
    logger.info("Prism-DB initialization and startup completed successfully")
    
    # Monitor processes
    try:
        while True:
            for name, process in list(processes.items()):
                if process.poll() is not None:
                    logger.error(f"{name} process terminated unexpectedly with code {process.returncode}")
                    logger.error(f"{name} stdout: {process.stdout.read() if process.stdout else 'N/A'}")
                    logger.error(f"{name} stderr: {process.stderr.read() if process.stderr else 'N/A'}")
                    # Attempt to restart the process
                    logger.info(f"Attempting to restart {name}...")
                    if name == "scheduler":
                        start_scheduler()
                    elif name == "agent_server":
                        start_agent_server()
            
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Caught keyboard interrupt. Shutting down...")
        signal_handler(None, None)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 