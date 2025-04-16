"""
Models implementations for the agents package.

This module serves as the entry point for the models subpackage.
"""

from typing import Any, Dict, List, Optional, Union
import json

from agents.models.gemini import GeminiModel


class Gemini:
    """Wrapper for Google's Gemini model.
    
    This class provides a complete method that was missing from the original
    Gemini implementation, causing the error.
    """
    
    def __init__(self, id: str = "gemini-2.0-flash-exp"):
        """Initialize the Gemini model.
        
        Args:
            id: Model identifier for Gemini.
        """
        self.id = id
        self.model = GeminiModel(id=id)
    
    async def predict(self, *args, **kwargs):
        """Delegate to the underlying model's predict method."""
        return await self.model.predict(*args, **kwargs)
        
    def complete(self, prompt: str, response_format: Optional[Dict[str, Any]] = None) -> Any:
        """Generate completion using the Gemini model.
        
        This method provides compatibility with the expected interface.
        
        Args:
            prompt: The prompt to generate a response for.
            response_format: Optional response format specification.
            
        Returns:
            A response object with a text attribute containing the generated text.
        """
        # Create a simple response object with the async predict method
        import asyncio
        response = asyncio.run(self.model.predict(prompt=prompt))
        
        # Extract the content from the response
        text = response.get("content", "")
        
        # Format the response if needed
        if response_format and response_format.get("type") == "json_object":
            # Ensure the response is valid JSON
            try:
                json.loads(text)
            except json.JSONDecodeError:
                # If not valid JSON, try to convert to proper JSON format
                text = json.dumps({"result": text})
        
        # Create a response object with a text attribute
        class Response:
            def __init__(self, text):
                self.text = text
                
        return Response(text)

# Export the Gemini class
__all__ = ["Gemini"] 