from abc import ABC, abstractmethod
import logging

class BaseAgent(ABC):
    """Base class for all PrismDB agents."""
    
    def __init__(self, name, config=None):
        """
        Initialize the base agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"prismdb.agent.{name}")
        self.shared_context = {}
    
    @abstractmethod
    async def process(self, message, context=None):
        """
        Process a message and return a response.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: The response from the agent
        """
        pass
    
    def update_context(self, key, value):
        """
        Update the shared context with a new key-value pair.
        
        Args:
            key (str): The key to update
            value (any): The value to set
        """
        self.shared_context[key] = value
        self.logger.debug(f"Updated context: {key}")
    
    def get_from_context(self, key, default=None):
        """
        Get a value from the shared context.
        
        Args:
            key (str): The key to retrieve
            default (any, optional): Default value if key doesn't exist
            
        Returns:
            any: The value from the context or default
        """
        return self.shared_context.get(key, default)
        
    def log_thought(self, thought):
        """
        Log a thought for visualization and monitoring.
        
        Args:
            thought (str): The thought to log
        """
        self.logger.info(f"THOUGHT: {thought}")
        # This will be extended to send to the monitor agent in the implementation 