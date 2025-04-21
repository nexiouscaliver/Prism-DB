"""
Base PrismAgent class for the PrismDB framework.

This module defines the base agent class that all specialized agents
(NLU, Query, Visualization) will inherit from.
"""
from typing import List, Dict, Any, Optional, Union
import json
import asyncio

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.models.anthropic.claude import Claude
from pydantic import BaseModel, Field

from app.config import get_model_config, GOOGLE_API_KEY, OPENAI_API_KEY


class AgentResponse(BaseModel):
    """Standardized response format for all PrismDB agents."""
    
    status: str = Field(..., description="Status of the agent response")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Errors if any")


class PrismAgent(Agent):
    """Base agent class for PrismDB framework.
    
    This class extends the Agno Agent class and provides common functionality
    for all PrismDB agents, including standardized error handling, response
    formatting, and tool integration.
    """
    
    def __init__(
        self,
        name: str,
        tools: List[Any] = None,
        system_prompt: Optional[str] = None,
        instructions: Optional[List[str]] = None,
        model_id: str = "gemini-2.0-flash",
        model: Optional[Any] = None,
    ):
        """Initialize a PrismAgent.
        
        Args:
            name: Agent name for identification and logging.
            tools: Additional tools to add to the agent beyond the default ones.
            system_prompt: Optional system prompt to override default.
            instructions: Optional list of instructions to add to defaults.
            model_id: Model identifier to use.
            model: Optional model instance to use instead of creating a new one.
        """
        # Default instructions all PrismDB agents should follow
        default_instructions = [
            "Always validate inputs before processing",
            "Return errors in standardized JSON format",
            "Provide concise, actionable responses",
            "Include metadata about processing steps taken"
        ]
        
        # Combine default and custom instructions
        all_instructions = default_instructions
        if instructions:
            all_instructions.extend(instructions)
            
        # Default tools all PrismDB agents should have access to
        default_tools = []
        
        # Combine default and custom tools
        all_tools = default_tools
        if tools:
            all_tools.extend(tools)
        
        # Initialize the model if not provided
        if model is None:
            model = self._initialize_model(model_id)
        
        # Initialize the parent Agno Agent class
        super().__init__(
            name=name,
            model=model,
            tools=all_tools,
            instructions=all_instructions,
            description=system_prompt,
            debug_mode=True,  # Log detailed debugging info
        )
    
    def _initialize_model(self, model_id: str):
        """Initialize a model based on the model_id.
        
        Args:
            model_id: The model identifier.
            
        Returns:
            Initialized model instance.
        """
        # Get model configuration from app config
        model_config = get_model_config(model_id)
        
        # Initialize based on model type
        if model_id.startswith("gpt-"):
            return OpenAIChat(
                id=model_id,
                api_key=OPENAI_API_KEY,
                temperature=model_config.get("temperature", 0.2),
                top_p=model_config.get("top_p", 0.95)
            )
        elif model_id.startswith("claude-"):
            return Claude(
                id="anthropic.claude-3-5-sonnet-20240620-v1:0" if "3-5-sonnet" in model_id else model_id,
                temperature=model_config.get("temperature", 0.2),
                top_p=model_config.get("top_p", 0.95)
            )
        else:  # Default to Gemini models
            return Gemini(
                id=model_id,
                api_key=GOOGLE_API_KEY,
                generation_config={
                    "temperature": model_config.get("temperature", 0.2),
                    "top_p": model_config.get("top_p", 0.95),
                    "top_k": model_config.get("top_k", 40),
                    "max_output_tokens": model_config.get("max_output_tokens", 2048),
                }
            )
        
    def format_response(self, status: str, message: str, data: Any = None, errors: List[Dict[str, Any]] = None) -> str:
        """Format agent response in a standardized structure.
        
        Args:
            status: Response status (success/error).
            message: Human-readable response message.
            data: Optional response data.
            errors: Optional list of errors.
            
        Returns:
            JSON string with standardized response format.
        """
        response = AgentResponse(
            status=status,
            message=message,
            data=data,
            errors=errors
        )
        
        return response.json()
    
    def error_response(self, message: str, errors: Union[str, List[Dict[str, Any]]] = None) -> str:
        """Generate a standardized error response.
        
        Args:
            message: Error message.
            errors: Detailed error information or list of errors.
            
        Returns:
            JSON string with standardized error response.
        """
        # Convert string error to list format if provided as string
        if isinstance(errors, str):
            errors = [{"message": errors, "type": "general"}]
            
        return self.format_response("error", message, errors=errors)
    
    def success_response(self, message: str, data: Any = None) -> str:
        """Generate a standardized success response.
        
        Args:
            message: Success message.
            data: Response data.
            
        Returns:
            JSON string with standardized success response.
        """
        return self.format_response("success", message, data=data)
        
    async def process(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process an input with the agent and return structured response.
        
        Args:
            input_text: Natural language input to process.
            context: Optional context dictionary to provide to the agent.
            
        Returns:
            Structured response as a dictionary.
        """
        try:
            # Add context to agent memory if provided
            if context:
                for key, value in context.items():
                    self.add_memory(f"{key}: {json.dumps(value)}")
            
            # Get response from Agno agent with JSON output format
            response = await self.generate(
                input_text, 
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse the response - assuming it's in our JSON format
            try:
                # Handle different response types
                if isinstance(response, str):
                    # Check if the response is wrapped in markdown code blocks and clean it
                    if response.strip().startswith("```") and response.strip().endswith("```"):
                        # Extract the content between the code block markers
                        lines = response.strip().split("\n")
                        # Remove the first line (```json) and the last line (```)
                        content_lines = lines[1:-1]
                        response = "\n".join(content_lines)
                    
                    # Parse the JSON response
                    parsed = json.loads(response)
                elif isinstance(response, dict):
                    # Already a dictionary
                    parsed = response
                else:
                    # Convert to string and try to parse
                    response_str = str(response)
                    if response_str.strip().startswith("```") and response_str.strip().endswith("```"):
                        lines = response_str.strip().split("\n")
                        content_lines = lines[1:-1]
                        response_str = "\n".join(content_lines)
                    
                    try:
                        parsed = json.loads(response_str)
                    except json.JSONDecodeError:
                        # If parsing fails, wrap in a standard response
                        return json.loads(self.success_response("Processing completed", {"result": response_str}))
                
                # Check if it has our expected keys
                if not all(k in parsed for k in ["status", "message"]):
                    # Convert to our standard format
                    result = {
                        "status": "success",
                        "message": "Processing completed",
                        "data": parsed
                    }
                    return result
                return parsed
            except json.JSONDecodeError:
                # If not JSON, wrap it in a standard success response
                return json.loads(self.success_response("Processing completed", {"result": response}))
                
        except Exception as e:
            return json.loads(self.error_response(f"Agent processing error: {str(e)}")) 