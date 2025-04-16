"""
Base PrismAgent class for the PrismDB framework.

This module defines the base agent class that all specialized agents
(NLU, Query, Visualization) will inherit from.
"""
from typing import List, Dict, Any, Optional, Union
import json

from agno.agent import Agent
from pydantic import BaseModel, Field

# Create a mock object instead of using the actual GeminiModel
class MockModel:
    def __init__(self, id="gemini-2.0-flash-exp"):
        self.id = id
        
    def get_provider(self):
        return "gemini"

from agents.tools.agno_sql_tools import PrismSQLTools
from agents.tools.schema import SchemaTool


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
        model_id: str = "gemini-2.0-flash-exp",
    ):
        """Initialize a PrismAgent.
        
        Args:
            name: Agent name for identification and logging.
            tools: Additional tools to add to the agent beyond the default ones.
            system_prompt: Optional system prompt to override default.
            instructions: Optional list of instructions to add to defaults.
            model_id: Google model identifier to use (default is Gemini Flash 2.0).
        """
        # Default instructions all PrismDB agents should follow
        default_instructions = [
            "Always validate SQL syntax before execution",
            "Map user terms to schema using context DB",
            "Return errors in standardized JSON format",
            "Provide concise, actionable responses",
            "Include metadata about processing steps taken",
            "Support queries across multiple databases when requested"
        ]
        
        # Combine default and custom instructions
        all_instructions = default_instructions
        if instructions:
            all_instructions.extend(instructions)
            
        # Default tools all PrismDB agents should have access to
        # Replace DatabaseTool with our new PrismSQLTools
        default_tools = [PrismSQLTools(), SchemaTool()]
        
        # Combine default and custom tools
        all_tools = default_tools
        if tools:
            all_tools.extend(tools)
        
        # Initialize the parent Agno Agent class
        super().__init__(
            name=name,
            model=MockModel(id=model_id),
            tools=all_tools,
            instructions=all_instructions,
            description=system_prompt,
            debug_mode=True,  # Log detailed debugging info
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
        
    def process(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
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
            
            # Get response from Agno agent
            response = self.generate(input_text)
            
            # Parse the response - assuming it's in our JSON format
            # If not, wrap it in a standard success response
            try:
                parsed = json.loads(response)
                # Check if it has our expected keys
                if not all(k in parsed for k in ["status", "message"]):
                    return json.loads(self.success_response("Processing completed", {"result": response}))
                return parsed
            except json.JSONDecodeError:
                return json.loads(self.success_response("Processing completed", {"result": response}))
                
        except Exception as e:
            return json.loads(self.error_response(f"Agent processing error: {str(e)}")) 