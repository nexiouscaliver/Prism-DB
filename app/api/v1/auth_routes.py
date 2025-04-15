"""
Authentication routes for the PrismDB API.

This module handles user authentication, JWT token generation and validation.
"""
from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pydantic import BaseModel, Field, EmailStr

from app.api.v1 import bp
from app import logger


class LoginRequest(BaseModel):
    """Pydantic model for login request validation."""
    
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


@bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate user and generate JWT token."""
    try:
        # Validate input with Pydantic
        data = request.get_json()
        login_request = LoginRequest(**data)
        
        # TODO: Implement actual user authentication
        logger.info("Login attempt", email=login_request.email)
        
        # Placeholder response - in production, validate credentials
        access_token = create_access_token(identity=login_request.email)
        
        return jsonify({
            "access_token": access_token
        })
    except Exception as e:
        logger.error("Login error", error=str(e))
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400


@bp.route("/auth/validate", methods=["GET"])
@jwt_required()
def validate_token():
    """Validate JWT token and return user identity."""
    current_user = get_jwt_identity()
    return jsonify({
        "status": "success",
        "user": current_user
    }) 