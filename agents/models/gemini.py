"""
Custom Gemini model implementation for Agno.

This module provides a custom implementation of the Gemini model for the Agno framework.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from agno.models.base import BaseModel
from agents.adapters.gemini_adapter import GeminiModelAdapter


class GeminiModel(BaseModel):
    """Google Gemini model implementation for the Agno framework."""
    
    def __init__(self, id: str = "gemini-2.0-flash-exp"):
        """Initialize the Gemini model.
        
        Args:
            id: Model identifier for Gemini.
        """
        super().__init__(id=id)
        self.adapter = GeminiModelAdapter(model_id=id)
    
    async def predict(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate a prediction from the Gemini model.
        
        Args:
            prompt: The prompt to generate a response for.
            system: Optional system prompt.
            temperature: Optional temperature parameter.
            max_tokens: Optional maximum tokens parameter.
            top_p: Optional top_p parameter.
            tools: Optional list of tool definitions.
            tool_choice: Optional tool choice parameter.
            **kwargs: Additional keyword arguments.
            
        Returns:
            Dictionary with the prediction result.
        """
        # Use the adapter to generate the response
        if tools:
            result = self.adapter.generate_with_tools(
                prompt=prompt,
                tools=tools,
                system_prompt=system
            )
            return {
                "content": result["response"],
                "tool_calls": result["tool_calls"]
            }
        else:
            content = self.adapter.generate(
                prompt=prompt,
                system_prompt=system
            )
            return {"content": content} 