"""
Base Tool implementation for PrismDB.

This module provides a BaseTool class that can be used as a foundation for
custom tools, replacing the dependency on agno.tools.base.
"""
from typing import Dict, Any, Optional


class BaseTool:
    """Base class for all tools in PrismDB.
    
    This class provides a foundation for implementing custom tools
    that can be used by agents in the PrismDB system.
    """
    
    name: str = "base_tool"
    description: str = "Base tool class for PrismDB"
    
    def __init__(self, **kwargs):
        """Initialize the base tool."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Run the tool with the provided arguments.
        
        Args:
            **kwargs: Arguments for the tool.
            
        Returns:
            Tool execution results.
        """
        raise NotImplementedError("Subclasses must implement the run method")
    
    def __str__(self) -> str:
        """Return a string representation of the tool."""
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        """Return a string representation of the tool."""
        return self.__str__() 