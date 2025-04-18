#!/usr/bin/env python
"""
PrismDB Lite - Natural Language to SQL Multi-Agent System

This is the main entry point for the PrismDB Lite application.
"""

import os
import sys
import logging
import asyncio
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

from agents.agent_factory import AgentFactory
from api.app import create_app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("prismdb")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PrismDB Lite - Natural Language to SQL Multi-Agent System")
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/agent_teams.yaml",
        help="Path to agent team configuration file"
    )
    
    parser.add_argument(
        "--env", 
        type=str, 
        default="development",
        choices=["development", "production"],
        help="Environment to use (development or production)"
    )
    
    parser.add_argument(
        "--mode", 
        type=str, 
        default=None,
        choices=["route", "coordinate", "collaborate"],
        help="Agent team processing mode (overrides the default from config)"
    )
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1",
        help="Host for the API server"
    )
    
    parser.add_argument(
        "--port", 
        type=str, 
        default="5000",
        help="Port for the API server"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (overrides the default from config)"
    )
    
    return parser.parse_args()

async def test_agents(agents, query: str = "Show me a list of all users"):
    """
    Test the agents with a simple query.
    
    Args:
        agents (dict): Dictionary of agents
        query (str, optional): Test query to process
    """
    logger.info(f"Testing agents with query: {query}")
    
    # Process the query through the orchestrator
    orchestrator = agents.get("orchestrator")
    if not orchestrator:
        logger.error("Orchestrator not available")
        return
    
    try:
        # Process the query
        result = await orchestrator.process({"query": query})
        
        # Pretty print the result
        result_json = json.dumps(result, indent=2)
        logger.info(f"Query result:\n{result_json}")
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")

async def init_agents(config_path: str, environment: str, mode: str = None):
    """
    Initialize the agents.
    
    Args:
        config_path (str): Path to agent team configuration file
        environment (str): Environment to use
        mode (str, optional): Processing mode to use
        
    Returns:
        dict: Dictionary of agents
    """
    logger.info(f"Initializing agents with config: {config_path}, environment: {environment}")
    
    # Create the agent team
    agents = AgentFactory.create_agent_team(config_path, environment)
    
    # Set the processing mode if specified
    if mode and "orchestrator" in agents:
        agents["orchestrator"].set_mode(mode)
        logger.info(f"Set processing mode to: {mode}")
    
    return agents

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_args()
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Configure logging
    if args.log_level:
        logger.setLevel(getattr(logging, args.log_level))
    
    # Get the absolute path to the config file
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), args.config)
    )
    
    # Make sure the config file exists
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Initialize agents
    try:
        agents = asyncio.run(init_agents(config_path, args.env, args.mode))
    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}")
        sys.exit(1)
    
    # Run a test query if in debug mode
    if args.debug:
        asyncio.run(test_agents(agents))
    
    # Create and run the API server
    app = create_app(agents)
    
    # Run the API server
    app.run(host=args.host, port=int(args.port), debug=args.debug)

if __name__ == "__main__":
    main() 