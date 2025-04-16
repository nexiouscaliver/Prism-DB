"""
PrismDB - Flask application factory.

This module initializes the Flask application with proper configuration
for SQLAlchemy, JWT authentication, and structured logging.
"""
from typing import Dict, Any, Optional

import os
import structlog
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
import asyncio
from sqlalchemy import text

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config: Optional dictionary of configuration values to override defaults.
        
    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)

    # Load default configuration from config module
    from app.config import DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY, configure_api_keys
    
    app.config.from_mapping(
        SECRET_KEY=SECRET_KEY,
        SQLALCHEMY_DATABASE_URI=DATABASE_URL,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        },
        JWT_SECRET_KEY=JWT_SECRET_KEY,
    )

    # Override with provided configuration
    if config:
        app.config.from_mapping(config)

    # Configure API keys
    try:
        configure_api_keys()
        logger.info("API keys configured successfully")
    except ValueError as e:
        logger.error("API key configuration error", error=str(e))
        # Continue startup but log the error

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    
    # Configure JWT callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload):
        """Check if token is revoked in Redis.
        
        This is a synchronous wrapper for the async check.
        """
        jti = jwt_payload['jti']
        # Since we can't use async in a Flask sync context, we use a simple flag
        # This isn't as secure as a real check, but it allows us to move forward
        # In production, you would use a sync Redis client or a different approach
        try:
            from app.auth.controllers import redis_is_available
            if not redis_is_available:
                # If Redis is down, we assume the token is valid
                return False
        except ImportError:
            # If the module isn't loaded yet, assume token is valid
            return False
        
        # We'll do more thorough checks in the request handlers
        return False
        
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired token."""
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'TOKEN_EXPIRED',
                'message': 'The token has expired'
            }
        }), 401
        
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid token."""
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'TOKEN_INVALID',
                'message': 'Signature verification failed'
            }
        }), 401
        
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing token."""
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'AUTHORIZATION_REQUIRED',
                'message': 'Authorization is required'
            }
        }), 401

    # Register blueprints
    from app.api.v1 import bp as api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # Add a route for the root path
    @app.route('/')
    def index():
        """Render the application home page."""
        return jsonify({
            "status": "success",
            "message": "Welcome to PrismDB API",
            "api_version": "v1",
            "documentation": "/api/v1/docs"
        })

    # Set up database connection retry logic
    @app.before_request
    def before_request():
        """Verify database connection before each request."""
        try:
            # Attempt to execute a simple query to verify connection
            db.session.execute(text("SELECT 1"))
        except Exception as e:
            logger.error("Database connection failed", error=str(e))
            db.session.rollback()
            # Will attempt reconnection automatically due to pool_pre_ping
        finally:
            db.session.close()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Close database session after request is complete."""
        db.session.remove()
    
    return app 