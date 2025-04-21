"""
Agent Orchestration Engine for Prism-DB.

This module handles the coordination and execution of multiple agents
to process user requests efficiently.
"""
import asyncio
from asyncio import gather
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import logging
import json

from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ai.agents.base import PrismAgent
from ai.agents.keai import KeaiAgent
from ai.agents.agent_factory import create_agent

logger = logging.getLogger(__name__)


# Pydantic models for the orchestrator
class AgentRequest(BaseModel):
    """Input parameters for agent execution."""
    
    query: str = Field(..., description="User query to process")
    user_id: str = Field(..., description="User ID for tracking and permissions")
    agent_type: str = Field("keai", description="Type of agent to use")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the agent")
    model_name: Optional[str] = Field(None, description="Model to use for the agent")
    
    @validator('query')
    def query_not_empty(cls, v):
        """Validate that query is not empty."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class AgentResponse(BaseModel):
    """Standardized response format for orchestrator."""
    
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Status of the request (success, error, processing)")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if status is error")
    processing_time: float = Field(..., description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of creation")


class Orchestrator:
    """Orchestrator for Prism-DB agents.
    
    This class coordinates the execution of multiple agents to process
    user requests efficiently.
    """
    
    def __init__(self):
        """Initialize the orchestrator with agent instances."""
        # Default agents can be initialized here if needed
        self.agents: Dict[str, PrismAgent] = {}
        
    def register_agent(self, agent_id: str, agent: PrismAgent) -> None:
        """Register an agent with the orchestrator.
        
        Args:
            agent_id: ID to register the agent under.
            agent: Agent instance to register.
        """
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id}")
        
    def get_agent(self, agent_id: str) -> Optional[PrismAgent]:
        """Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to get.
            
        Returns:
            Agent instance or None if not found.
        """
        return self.agents.get(agent_id)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def process_query(self, request: AgentRequest) -> Dict[str, Any]:
        """Process a user query.
        
        Args:
            request: User request parameters.
            
        Returns:
            Query results.
        """
        start_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        
        try:
            # Get or create the appropriate agent
            agent = self._get_or_create_agent(request.agent_type, request.model_name)
            
            # Process the query with the agent
            context = request.context or {}
            context["user_id"] = request.user_id
            
            # Execute the agent
            result = agent.process(request.query, context)
            
            # Handle coroutines - if process returns a coroutine, await it
            if asyncio.iscoroutine(result):
                result = await result
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create the response
            response = AgentResponse(
                request_id=request_id,
                status="success",
                result=result,
                processing_time=processing_time,
                created_at=start_time
            )
            
            return response.dict()
            
        except Exception as e:
            # Calculate processing time even for errors
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log the error
            logger.exception(f"Error processing query: {str(e)}")
            
            # Create error response
            response = AgentResponse(
                request_id=request_id,
                status="error",
                error=str(e),
                processing_time=processing_time,
                created_at=start_time
            )
            
            return response.dict()
    
    async def process_multi_queries(self, requests: List[AgentRequest]) -> List[Dict[str, Any]]:
        """Process multiple queries in parallel.
        
        Args:
            requests: List of user request parameters.
            
        Returns:
            List of query results.
        """
        tasks = [self.process_query(request) for request in requests]
        return await gather(*tasks)
    
    def _get_or_create_agent(self, agent_type: str, model_name: Optional[str] = None) -> PrismAgent:
        """Get an existing agent or create a new one.
        
        Args:
            agent_type: Type of agent to get or create.
            model_name: Model to use for the agent.
            
        Returns:
            Agent instance.
        """
        # Create a unique agent ID based on type and model
        agent_id = f"{agent_type}_{model_name or 'default'}"
        
        # Check if we already have this agent
        agent = self.get_agent(agent_id)
        if agent:
            return agent
        
        # Create a new agent
        agent = create_agent(
            agent_type=agent_type,
            name=agent_type.capitalize(),
            model_name=model_name,
        )
        
        # Register the agent
        self.register_agent(agent_id, agent)
        
        return agent


# Global orchestrator instance
orchestrator = Orchestrator()


async def process_query(
    query: str,
    user_id: str,
    agent_type: str = "keai",
    context: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Process a user query using the orchestrator.
    
    This is a convenience function for processing a single query.
    
    Args:
        query: User query to process.
        user_id: User ID for tracking and permissions.
        agent_type: Type of agent to use.
        context: Additional context for the agent.
        model_name: Model to use for the agent.
        
    Returns:
        Query results.
    """
    request = AgentRequest(
        query=query,
        user_id=user_id,
        agent_type=agent_type,
        context=context,
        model_name=model_name,
    )
    
    return await orchestrator.process_query(request)


# Synchronous wrapper for process_query
def process_query_sync(
    query: str,
    user_id: str,
    agent_type: str = "keai",
    context: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Process a user query synchronously using the orchestrator.
    
    This is a convenience function for processing a single query.
    
    Args:
        query: User query to process.
        user_id: User ID for tracking and permissions.
        agent_type: Type of agent to use.
        context: Additional context for the agent.
        model_name: Model to use for the agent.
        
    Returns:
        Query results.
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            process_query(
                query=query,
                user_id=user_id,
                agent_type=agent_type,
                context=context,
                model_name=model_name,
            )
        )
        return result
    finally:
        loop.close() 