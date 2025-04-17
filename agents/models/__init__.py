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
    
    def __init__(self, id: str = "gemini-2.0-flash-exp", api_key: Optional[str] = None, 
                 generation_config: Optional[Dict[str, Any]] = None):
        """Initialize the Gemini model.
        
        Args:
            id: Model identifier for Gemini.
            api_key: Optional API key for Gemini.
            generation_config: Optional generation configuration.
        """
        self.id = id
        self.model = GeminiModel(id=id, api_key=api_key, generation_config=generation_config)
    
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
        
    def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None) -> Any:
        """Generate content using the Gemini model.
        
        This method provides compatibility with the newer Gemini API.
        
        Args:
            prompt: The prompt to generate a response for.
            generation_config: Optional generation configuration.
            
        Returns:
            A response object with a text attribute containing the generated text.
        """
        # Convert generation_config to response_format if needed
        response_format = None
        if generation_config and "response_mime_type" in generation_config:
            if generation_config["response_mime_type"] == "application/json":
                response_format = {"type": "json_object"}
        
        # Call the complete method which handles the actual generation
        return self.complete(prompt=prompt, response_format=response_format)

# Export the Gemini class
__all__ = ["Gemini"] 