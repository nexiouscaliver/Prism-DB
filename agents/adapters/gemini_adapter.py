"""
Google Gemini Adapter for Agno integration.

This module provides the necessary adapters to ensure that Google's Gemini models
work properly with the Agno framework.
"""
import json
from typing import Any, Dict, List, Optional, Union

import google.generativeai as genai
from app.config import GOOGLE_API_KEY, get_model_config

# Configure Google API key
genai.configure(api_key=GOOGLE_API_KEY)


class GeminiModelAdapter:
    """Adapter class for Gemini models to work with Agno framework."""
    
    def __init__(self, model_id: str = "gemini-2.0-flash-exp"):
        """Initialize the Gemini model adapter.
        
        Args:
            model_id: ID of the Gemini model to use.
        """
        self.model_id = model_id
        self.config = get_model_config(model_id)
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(
                model_name=model_id,
                generation_config=genai.GenerationConfig(
                    temperature=self.config["temperature"],
                    top_p=self.config["top_p"],
                    top_k=self.config["top_k"],
                    max_output_tokens=self.config["max_output_tokens"],
                    response_mime_type="text/plain",
                )
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini model {model_id}: {str(e)}")
    
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a response using the Gemini model.
        
        Args:
            prompt: The prompt to generate a response for.
            system_prompt: Optional system prompt for the model.
            tools: Optional list of tool definitions.
            
        Returns:
            Generated text response.
        """
        # Create the chat session
        chat = self.model.start_chat(history=[])
        
        # Add system prompt if provided
        if system_prompt:
            chat.send_message(system_prompt)
        
        # Configure tools if provided
        if tools:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=self.config["temperature"],
                    top_p=self.config["top_p"],
                    top_k=self.config["top_k"],
                    max_output_tokens=self.config["max_output_tokens"],
                ),
                tools=tools
            )
            return response.text
        
        # Send the message and get the response
        response = chat.send_message(prompt)
        return response.text
    
    def generate_with_tools(self, 
                          prompt: str, 
                          tools: List[Dict[str, Any]],
                          system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate a response with tool calling using the Gemini model.
        
        Args:
            prompt: The prompt to generate a response for.
            tools: List of tool definitions.
            system_prompt: Optional system prompt for the model.
            
        Returns:
            Dictionary with response and tool calls.
        """
        # Format tools for Gemini
        formatted_tools = []
        for tool in tools:
            formatted_tool = {
                "function_declarations": [{
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": tool.get("parameters", {}).get("properties", {}),
                        "required": tool.get("parameters", {}).get("required", [])
                    }
                }]
            }
            formatted_tools.append(formatted_tool)
        
        # Create the chat session
        chat = self.model.start_chat(history=[])
        
        # Add system prompt if provided
        if system_prompt:
            chat.send_message(system_prompt)
        
        # Send the message with tools and get the response
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=self.config["temperature"],
                top_p=self.config["top_p"],
                top_k=self.config["top_k"],
                max_output_tokens=self.config["max_output_tokens"],
            ),
            tools=formatted_tools
        )
        
        # Extract tool calls if available
        tool_calls = []
        try:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call'):
                        tool_calls.append({
                            "name": part.function_call.name,
                            "arguments": json.loads(part.function_call.args),
                        })
        except Exception:
            # No tool calls or parsing error
            pass
            
        return {
            "response": response.text,
            "tool_calls": tool_calls
        } 