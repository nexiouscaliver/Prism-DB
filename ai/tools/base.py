"""
Tool utilities for Prism-DB framework.

This module provides utility functions and classes for working with tools.
"""
from typing import Dict, Any, Optional, List
import json
import logging

logger = logging.getLogger(__name__)


class ToolResponseFormatter:
    """Utility class for formatting tool responses in a standard way."""
    
    @staticmethod
    def format_success_response(message: str, data: Any = None) -> Dict[str, Any]:
        """Format a successful response.
        
        Args:
            message: Human-readable message.
            data: Response data.
            
        Returns:
            Formatted success response.
        """
        response = {
            "status": "success",
            "message": message,
        }
        
        if data is not None:
            response["data"] = data
            
        return response
    
    @staticmethod
    def format_error_response(message: str, errors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Format an error response.
        
        Args:
            message: Human-readable error message.
            errors: List of detailed error information.
            
        Returns:
            Formatted error response.
        """
        response = {
            "status": "error",
            "message": message,
        }
        
        if errors is not None:
            response["errors"] = errors
            
        return response 