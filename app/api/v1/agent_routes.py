"""
Agent routes for the PrismDB API.

This module handles agent management, configuration, and monitoring.
"""
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import asyncio

from app.api.v1 import bp
from app import logger
from ai.agents.orchestrator import orchestrator, process_query_sync, AgentRequest


class AgentConfigRequest(BaseModel):
    """Pydantic model for agent configuration request validation."""
    
    agent_id: str = Field(..., description="Agent identifier")
    config: dict = Field(..., description="Agent configuration")


class QueryRequest(BaseModel):
    """Pydantic model for agent query request validation."""
    
    query: str = Field(..., description="User query to process")
    agent_type: str = Field("keai", description="Type of agent to use")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the agent")
    model_name: Optional[str] = Field(None, description="Model to use for the agent")
    
    @validator('query')
    def query_not_empty(cls, v):
        """Validate that query is not empty."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


@bp.route("/agents", methods=["GET"])
@jwt_required()
def list_agents():
    """List all available agents."""
    agents = [
        {"id": "keai", "name": "KEAI Agent", "status": "active", "description": "Knowledge-enhanced AI assistant"},
        {"id": "prism", "name": "Prism Agent", "status": "active", "description": "Basic Prism agent framework"},
    ]
    
    return jsonify({
        "status": "success",
        "agents": agents
    })


@bp.route("/agents/<agent_id>", methods=["GET"])
@jwt_required()
def get_agent(agent_id):
    """Get agent configuration and status."""
    logger.info("Retrieving agent", agent_id=agent_id)
    
    # Get agent information based on agent_id
    if agent_id == "keai":
        agent_info = {
            "id": "keai",
            "name": "KEAI Agent",
            "status": "active",
            "description": "Knowledge-enhanced AI assistant",
            "features": [
                "Web search",
                "Financial data",
                "Document analysis",
                "Research reporting"
            ],
            "config": {
                "google_search": True,
                "exa_search": True,
                "finance_tools": True,
                "model_name": "gpt-4o-mini"
            }
        }
    elif agent_id == "prism":
        agent_info = {
            "id": "prism",
            "name": "Prism Agent",
            "status": "active",
            "description": "Basic Prism agent framework",
            "features": [
                "Natural language processing",
                "Structured response formatting",
                "Tool integration"
            ],
            "config": {
                "model_name": "gemini-2.0-flash"
            }
        }
    else:
        return jsonify({
            "status": "error",
            "message": f"Agent {agent_id} not found"
        }), 404
    
    return jsonify({
        "status": "success",
        "agent": agent_info
    })


@bp.route("/agents/<agent_id>/config", methods=["POST"])
@jwt_required()
def configure_agent(agent_id):
    """Update agent configuration."""
    try:
        # Validate input with Pydantic
        data = request.get_json()
        config_request = AgentConfigRequest(agent_id=agent_id, config=data.get("config", {}))
        
        logger.info("Configuring agent", 
                   agent_id=config_request.agent_id, 
                   config=config_request.config)
        
        # TODO: Implement actual agent configuration
        # For now, just return success
        
        return jsonify({
            "status": "success",
            "message": "Agent configuration updated",
            "agent_id": config_request.agent_id
        })
    except Exception as e:
        logger.error("Agent configuration error", error=str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@bp.route("/agents/<agent_id>/query", methods=["POST"])
@jwt_required()
def query_agent(agent_id):
    """Send a query to an agent."""
    try:
        # Get the current user
        user_id = get_jwt_identity()
        
        # Validate input with Pydantic
        data = request.get_json()
        query_request = QueryRequest(
            query=data.get("query", ""),
            agent_type=agent_id,
            context=data.get("context"),
            model_name=data.get("model_name")
        )
        
        logger.info("Processing agent query", 
                   agent_id=agent_id, 
                   query=query_request.query)
        
        # Process the query using our orchestrator
        result = process_query_sync(
            query=query_request.query,
            user_id=user_id,
            agent_type=agent_id,
            context=query_request.context,
            model_name=query_request.model_name
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("Agent query error", error=str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400 