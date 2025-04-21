from typing import Optional, List, Dict, Any
from agno.agent import Agent
from agno.tools import Toolkit

from .keai import KeaiAgent
from agents.base import PrismAgent  # Import directly from agents.base


def get_web_agent(
    agent_type: str,
    model_name: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tools: Optional[List[Toolkit]] = None,
    system_prompt: Optional[str] = None,
    instructions: Optional[List[str]] = None,
) -> Agent:
    """Return the agent based on agent_type
    
    Args:
        agent_type: Type of agent to create.
        model_name: Name of the model to use.
        session_id: Session ID for the agent.
        user_id: User ID for the agent.
        tools: Additional tools to add to the agent.
        system_prompt: System prompt for the agent.
        instructions: Additional instructions for the agent.
        
    Returns:
        Initialized agent instance.
    """
    if agent_type == "keai":
        return KeaiAgent(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
            user_id=user_id,
            google_search=True,
            exa_search=True,
            tavily_search=True,
            finance_tools=True,
            risk_memo_tool=True,
            firecrawl_tool=True,
            research_agent=True,
            url_research_agent=True,
        )
    elif agent_type == "prism":
        return PrismAgent(
            name="PrismAgent",
            model_id=model_name,
            tools=tools,
            system_prompt=system_prompt,
            instructions=instructions,
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def get_local_agent(
    agent_type: str,
    model_name: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_google_search: bool = True,
    tools: Optional[List[Toolkit]] = None,
    system_prompt: Optional[str] = None,
    instructions: Optional[List[str]] = None,
) -> Agent:
    """Return the agent based on agent_type for local execution
    
    Args:
        agent_type: Type of agent to create.
        model_name: Name of the model to use.
        session_id: Session ID for the agent.
        user_id: User ID for the agent.
        use_google_search: Whether to enable Google search.
        tools: Additional tools to add to the agent.
        system_prompt: System prompt for the agent.
        instructions: Additional instructions for the agent.
        
    Returns:
        Initialized agent instance.
    """
    if agent_type == "keai":
        return KeaiAgent(
            model_name=model_name,
            tools=tools,
            session_id=session_id,
            user_id=user_id,
            google_search=use_google_search,
        )
    elif agent_type == "prism":
        return PrismAgent(
            name="PrismAgent",
            model_id=model_name,
            tools=tools,
            system_prompt=system_prompt,
            instructions=instructions,
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def create_agent(
    agent_type: str,
    name: str,
    model_name: Optional[str] = None,
    tools: Optional[List[Toolkit]] = None,
    system_prompt: Optional[str] = None,
    instructions: Optional[List[str]] = None,
) -> PrismAgent:
    """Create a new PrismAgent instance with the specified parameters.
    
    Args:
        agent_type: Type of agent to create.
        name: Name of the agent.
        model_name: Name of the model to use.
        tools: Tools to add to the agent.
        system_prompt: System prompt for the agent.
        instructions: Instructions for the agent.
        
    Returns:
        Initialized PrismAgent instance.
    """
    if agent_type == "prism":
        return PrismAgent(
            name=name,
            model_id=model_name,
            tools=tools,
            system_prompt=system_prompt,
            instructions=instructions,
        )
    elif agent_type == "keai":
        return KeaiAgent(
            model_name=model_name,
            tools=tools,
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
