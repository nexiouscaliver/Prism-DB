"""
PrismDB API v1 Blueprint.

This module defines the API v1 routes for the application.
"""
from flask import Blueprint

bp = Blueprint("api_v1", __name__)

# Import routes after blueprint creation to avoid circular imports
from app.api.v1 import query_routes, auth_routes, agent_routes, database_routes 