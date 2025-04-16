"""
Query processing routes for the PrismDB API.

This module handles the submission and processing of natural language queries.
"""
import asyncio
from flask import jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError

from app.api.v1 import bp
from app import logger
from app.auth.controllers import check_rate_limit, AuthErrorCode
from agents.orchestrator import Orchestrator, SQLGenerationInput


# Create an instance of the orchestrator
orchestrator = Orchestrator()


@bp.route("/query/generate", methods=["POST"])
@jwt_required()
async def generate_query():
    """Generate SQL from natural language query.
    
    This endpoint processes a natural language query through the agent orchestration
    pipeline to generate SQL.
    """
    try:
        # Get user identity from JWT
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # Validate input
        data = request.get_json()
        query = data.get("query", "")
        db_id = data.get("db_id", "default")
        
        # Check rate limit
        is_limited, remaining = await check_rate_limit(user_id)
        if is_limited:
            logger.warning("Rate limit exceeded", user_id=user_id)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": f"Rate limit exceeded. Try again in {remaining} seconds."
                }
            }), 429
        
        if not query:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Query cannot be empty"
                }
            }), 400
        
        # Process query through orchestrator
        context = {
            "user_id": user_id,
            "db_id": db_id
        }
        
        result = await orchestrator.process_query(query, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("Query generation error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while processing your request."
            }
        }), 500

@bp.route("/query/multi-db", methods=["POST"])
@jwt_required()
async def generate_multi_db_query():
    """Generate and execute a query across multiple databases.
    
    This endpoint processes a natural language query across all available databases.
    """
    try:
        # Get user identity from JWT
        user_id = get_jwt_identity()
        
        # Validate input
        data = request.get_json()
        query = data.get("query", "")
        
        # Check rate limit
        is_limited, remaining = await check_rate_limit(user_id)
        if is_limited:
            logger.warning("Rate limit exceeded", user_id=user_id)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": f"Rate limit exceeded. Try again in {remaining} seconds."
                }
            }), 429
        
        if not query:
            return jsonify({
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Query cannot be empty"
                }
            }), 400
        
        # Process query through orchestrator
        context = {
            "user_id": user_id,
            "multi_db": True
        }
        
        result = await orchestrator.process_multi_db_query(query, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("Multi-DB query generation error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while processing your request."
            }
        }), 500

@bp.route("/databases", methods=["GET"])
@jwt_required()
async def list_databases():
    """List all available databases.
    
    This endpoint returns information about all available databases.
    """
    try:
        # Get databases from query agent
        databases = orchestrator.query_agent.get_available_databases()
        
        return jsonify({
            "status": "success",
            "databases": databases
        })
        
    except Exception as e:
        logger.error("Database listing error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while retrieving databases."
            }
        }), 500

@bp.route("/query/execute", methods=["POST"])
@jwt_required()
async def execute_query():
    """Execute a generated SQL query.
    
    This endpoint executes a previously generated SQL query against the database.
    """
    try:
        # Get user identity from JWT
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        
        # Get query data from request
        data = request.get_json()
        sql = data.get("sql", "")
        db_id = data.get("db_id", "default")
        
        # Check user permissions
        user_prisms = jwt_data.get("prisms", [])
        required_permission = f"{db_id}::write" if sql.lower().startswith(("insert", "update", "delete")) else f"{db_id}::read"
        
        if required_permission not in user_prisms:
            logger.warning("Insufficient permissions for query execution", user_id=user_id, db_id=db_id)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.INSUFFICIENT_PERMISSIONS,
                    "message": f"You do not have {required_permission} access"
                }
            }), 403
        
        # Execute the query on the specified database
        params = data.get("parameters", {})
        query_result = await orchestrator.query_agent.execute_query(sql, params, db_id=db_id)
        
        return jsonify(query_result)
        
    except Exception as e:
        logger.error("Query execution error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while executing your query."
            }
        }), 500 