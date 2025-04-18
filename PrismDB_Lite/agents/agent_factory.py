import logging
import importlib
import yaml
import os
from typing import Dict, Any, Type, Optional

from .base import BaseAgent
from .orchestrator import Orchestrator
from .nlu_agent import NLUAgent
from .schema_agent import SchemaAgent
from .sql_agent import SQLAgent
from .execution_agent import ExecutionAgent
from .visualization_agent import VisualizationAgent
from .monitor_agent import MonitorAgent

logger = logging.getLogger("prismdb.agent_factory")

class AgentFactory:
    """
    Factory for creating and configuring agents based on configuration.
    """
    
    # Mapping of agent types to agent classes
    AGENT_TYPES = {
        "Orchestrator": Orchestrator,
        "NLUAgent": NLUAgent,
        "SchemaAgent": SchemaAgent,
        "SQLAgent": SQLAgent,
        "ExecutionAgent": ExecutionAgent,
        "VisualizationAgent": VisualizationAgent,
        "MonitorAgent": MonitorAgent
    }
    
    @classmethod
    def create_agent(cls, agent_type: str, name: str, config: Dict[str, Any] = None) -> BaseAgent:
        """
        Create an agent of the specified type.
        
        Args:
            agent_type (str): Type of agent to create
            name (str): Name for the agent
            config (dict, optional): Configuration for the agent
            
        Returns:
            BaseAgent: The created agent
        """
        # Check if the agent type is supported
        if agent_type not in cls.AGENT_TYPES:
            raise ValueError(f"Unsupported agent type: {agent_type}")
        
        # Create the agent
        agent_class = cls.AGENT_TYPES[agent_type]
        agent = agent_class(name=name, config=config)
        
        logger.info(f"Created agent: {name} (type: {agent_type})")
        return agent
    
    @classmethod
    def create_agent_team(cls, config_path: str, environment: str = "development") -> Dict[str, BaseAgent]:
        """
        Create a team of agents based on a configuration file.
        
        Args:
            config_path (str): Path to the agent team configuration file
            environment (str, optional): Environment to use (development, production, etc.)
            
        Returns:
            dict: Dictionary of agents keyed by name
        """
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
            raise ValueError(f"Failed to load configuration: {str(e)}")
        
        # Get environment config
        env_config = config.get("environments", {}).get(environment, {})
        
        # Get team config
        team_configs = config.get("teams", {})
        if not team_configs:
            raise ValueError("No team configurations found")
        
        # Use the first team in the config if there are multiple
        team_name = next(iter(team_configs))
        team_config = team_configs[team_name]
        
        agents = {}
        
        # Create orchestrator first
        if "orchestrator" in team_config.get("agents", {}):
            orchestrator_config = team_config["agents"]["orchestrator"]
            orchestrator = cls.create_agent(
                agent_type=orchestrator_config.get("type", "Orchestrator"),
                name="orchestrator",
                config=env_config
            )
            agents["orchestrator"] = orchestrator
        
        # Create all other agents
        for agent_name, agent_config in team_config.get("agents", {}).items():
            if agent_name == "orchestrator":
                continue  # Already created
            
            # Combine environment config with agent config
            combined_config = env_config.copy()
            combined_config.update(agent_config)
            
            # Ensure we have the required config for AI APIs
            if agent_name == "nlu_agent":
                combined_config["openai_api_key"] = env_config.get("apis", {}).get("openai", {}).get("api_key")
                combined_config["gemini_api_key"] = env_config.get("apis", {}).get("gemini", {}).get("api_key")
            elif agent_name == "sql_agent":
                combined_config["gemini_api_key"] = env_config.get("apis", {}).get("gemini", {}).get("api_key")
            
            # Add database configuration if relevant
            if agent_name in ["schema_agent", "execution_agent"]:
                combined_config["connection_string"] = env_config.get("database", {}).get("connection_string")
                combined_config["pool_size"] = env_config.get("database", {}).get("pool_size")
                combined_config["max_overflow"] = env_config.get("database", {}).get("max_overflow")
            
            # Create the agent
            agent = cls.create_agent(
                agent_type=agent_config.get("type", agent_name),
                name=agent_name,
                config=combined_config
            )
            
            # Register with orchestrator if available
            if "orchestrator" in agents:
                agents["orchestrator"].register_agent(agent_name, agent)
            
            agents[agent_name] = agent
        
        # Set the processing mode for the orchestrator
        if "orchestrator" in agents and "modes" in team_config:
            modes = team_config["modes"]
            if modes and len(modes) > 0:
                agents["orchestrator"].set_mode(modes[0])
        
        logger.info(f"Created agent team with {len(agents)} agents")
        return agents
    
    @classmethod
    def load_environment_variables(cls, config_path: str, environment: str = "development") -> Dict[str, str]:
        """
        Load necessary environment variables from a configuration file.
        
        Args:
            config_path (str): Path to the configuration file
            environment (str, optional): Environment to use
            
        Returns:
            dict: Dictionary of environment variables to set
        """
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {str(e)}")
            raise ValueError(f"Failed to load configuration: {str(e)}")
        
        # Get environment config
        env_config = config.get("environments", {}).get(environment, {})
        
        env_vars = {}
        
        # Extract API keys
        apis = env_config.get("apis", {})
        for api_name, api_config in apis.items():
            for key, value in api_config.items():
                env_name = f"{api_name.upper()}_{key.upper()}"
                if "${" in value and "}" in value:
                    # This is a reference to an environment variable
                    var_name = value.strip("${}")
                    env_vars[env_name] = os.environ.get(var_name, "")
                else:
                    env_vars[env_name] = value
        
        # Extract database config
        db_config = env_config.get("database", {})
        if "connection_string" in db_config:
            conn_string = db_config["connection_string"]
            if "${" in conn_string and "}" in conn_string:
                # Parse the connection string to extract the variables
                for var in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]:
                    if f"${{{var}}}" in conn_string:
                        env_vars[var] = os.environ.get(var, "")
        
        return env_vars
    
    @classmethod
    def register_custom_agent_type(cls, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register a custom agent type.
        
        Args:
            agent_type (str): Type name for the agent
            agent_class (Type[BaseAgent]): Agent class
        """
        if agent_type in cls.AGENT_TYPES:
            logger.warning(f"Overriding existing agent type: {agent_type}")
        
        cls.AGENT_TYPES[agent_type] = agent_class
        logger.info(f"Registered custom agent type: {agent_type}")
    
    @classmethod
    def load_custom_agent_from_path(cls, module_path: str, class_name: str, agent_type: Optional[str] = None) -> None:
        """
        Load a custom agent class from a Python module.
        
        Args:
            module_path (str): Import path to the module
            class_name (str): Name of the agent class in the module
            agent_type (str, optional): Type name for the agent (defaults to class name)
        """
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Ensure it's a subclass of BaseAgent
            if not issubclass(agent_class, BaseAgent):
                raise TypeError(f"Class {class_name} must be a subclass of BaseAgent")
            
            # Register the agent type
            agent_type = agent_type or class_name
            cls.register_custom_agent_type(agent_type, agent_class)
            
        except (ImportError, AttributeError, TypeError) as e:
            logger.error(f"Failed to load custom agent: {str(e)}")
            raise ValueError(f"Failed to load custom agent: {str(e)}") 