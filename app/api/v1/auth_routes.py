"""
Authentication routes for the PrismDB API.

This module handles user authentication, JWT token generation, validation, and revocation.
"""
import asyncio
from functools import wraps

from flask import jsonify, request, abort
from flask_jwt_extended import (
    jwt_required, 
    get_jwt_identity, 
    get_jwt,
    verify_jwt_in_request,
    current_user
)
from pydantic import BaseModel, ValidationError

from app.api.v1 import bp
from app import logger
from app.auth.controllers import (
    AuthRequest,
    TokenResponse,
    AuthErrorCode,
    authenticate_user,
    generate_tokens,
    check_rate_limit,
    revoke_token,
    is_token_valid,
    get_token_data
)


def requires_role(role: str):
    """Decorator to check if the current user has the required role.
    
    Args:
        role: Role required to access this endpoint
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            # Verify the JWT is valid
            verify_jwt_in_request()
            
            # Get the JWT claims
            claims = get_jwt()
            
            # Check if the user has the required role
            if claims.get("role") != role:
                abort(403, description=f"Insufficient permissions: {AuthErrorCode.INSUFFICIENT_PERMISSIONS}")
                
            return await f(*args, **kwargs)
        return wrapper
    return decorator


def requires_prism(prism: str):
    """Decorator to check if the current user has access to the required prism.
    
    Args:
        prism: Prism access required (format: "db_name::permission")
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            # Verify the JWT is valid
            verify_jwt_in_request()
            
            # Get the JWT claims
            claims = get_jwt()
            
            # Check if the user has access to the required prism
            user_prisms = claims.get("prisms", [])
            if prism not in user_prisms:
                abort(403, description=f"Insufficient prism access: {AuthErrorCode.INSUFFICIENT_PERMISSIONS}")
                
            return await f(*args, **kwargs)
        return wrapper
    return decorator


@bp.route("/auth/login", methods=["POST"])
async def login():
    """Authenticate user and generate JWT tokens.
    
    This endpoint validates username/password, generates JWT tokens,
    and stores token fingerprints in Redis with user role.
    """
    try:
        # Validate input with Pydantic
        data = request.get_json()
        login_request = AuthRequest(**data)
        
        # Check rate limit
        is_limited, remaining = await check_rate_limit(login_request.username)
        if is_limited:
            logger.warning("Rate limit exceeded", username=login_request.username)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.RATE_LIMIT_EXCEEDED,
                    "message": f"Rate limit exceeded. Try again in {remaining} seconds."
                }
            }), 429
        
        # Authenticate user
        success, user_data, error_code = await authenticate_user(
            login_request.username, 
            login_request.password
        )
        
        if not success:
            logger.warning("Login failed", username=login_request.username, error=error_code)
            return jsonify({
                "status": "error",
                "error": {
                    "code": error_code,
                    "message": "Invalid username or password."
                }
            }), 401
        
        # Generate tokens
        tokens = await generate_tokens(user_data["id"])
        
        # Create Pydantic model for response validation
        response = TokenResponse(**tokens)
        
        logger.info("Login successful", username=login_request.username)
        return jsonify(response.dict())
        
    except ValidationError as e:
        logger.error("Validation error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }
        }), 400
        
    except Exception as e:
        logger.error("Login error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while processing your request."
            }
        }), 500


@bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
async def refresh():
    """Refresh access token using refresh token.
    
    This endpoint validates the refresh token and generates a new access token.
    """
    try:
        # Get user identity and JWT ID
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        token_id = jwt_data.get("jti")
        
        # Verify token is valid in Redis
        if not await is_token_valid(token_id):
            logger.warning("Refresh token invalid", user_id=user_id)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.TOKEN_INVALID,
                    "message": "Invalid refresh token."
                }
            }), 401
        
        # Generate new access token
        tokens = await generate_tokens(user_id)
        
        # Revoke old refresh token if we're also returning a new refresh token
        await revoke_token(token_id)
        
        # Create Pydantic model for response validation
        response = TokenResponse(**tokens)
        
        logger.info("Token refreshed", user_id=user_id)
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error("Refresh error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while processing your request."
            }
        }), 500


@bp.route("/auth/revoke", methods=["POST"])
@jwt_required()
async def revoke():
    """Revoke the current token.
    
    This endpoint revokes the current JWT token by removing it from Redis.
    """
    try:
        # Get JWT data
        jwt_data = get_jwt()
        token_id = jwt_data.get("jti")
        user_id = get_jwt_identity()
        
        # Revoke token
        success = await revoke_token(token_id)
        
        if not success:
            logger.warning("Token already revoked", user_id=user_id)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.TOKEN_INVALID,
                    "message": "Token already revoked or invalid."
                }
            }), 400
        
        logger.info("Token revoked", user_id=user_id)
        return jsonify({
            "status": "success",
            "message": "Token revoked successfully."
        })
        
    except Exception as e:
        logger.error("Revoke error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while processing your request."
            }
        }), 500


@bp.route("/auth/validate", methods=["GET"])
@jwt_required()
async def validate_token():
    """Validate JWT token and return user identity and permissions.
    
    This endpoint validates the JWT token and returns the user's identity and permissions.
    """
    try:
        # Get JWT data
        user_id = get_jwt_identity()
        jwt_data = get_jwt()
        token_id = jwt_data.get("jti")
        
        # Get additional token data from Redis
        token_data = await get_token_data(token_id)
        
        if not token_data:
            logger.warning("Token not found in Redis", user_id=user_id)
            return jsonify({
                "status": "error",
                "error": {
                    "code": AuthErrorCode.TOKEN_INVALID,
                    "message": "Invalid token or token revoked."
                }
            }), 401
        
        return jsonify({
            "status": "success",
            "user": {
                "id": user_id,
                "role": jwt_data.get("role", ""),
                "prisms": jwt_data.get("prisms", [])
            }
        })
        
    except Exception as e:
        logger.error("Validate error", error=str(e))
        return jsonify({
            "status": "error",
            "error": {
                "code": "SERVER_ERROR",
                "message": "An error occurred while processing your request."
            }
        }), 500 