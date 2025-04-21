"""
Compatibility module for PrismAgent.

This module re-exports the PrismAgent class from agents.base for backward compatibility.
"""

from agents.base import PrismAgent, AgentResponse

# Re-export for backward compatibility
__all__ = ['PrismAgent', 'AgentResponse'] 