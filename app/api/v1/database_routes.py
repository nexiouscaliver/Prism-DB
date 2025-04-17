"""
Database Routes for PrismDB API.

This module defines the API routes for database operations including:
- Listing available databases
- Getting schema information
- Extracting schema from databases to the default database
- Selecting a database for operations
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required

from app.api.v1 import bp
from services.database_service import DatabaseService

# Initialize database service
db_service = DatabaseService()


@bp.route("/databases", methods=["GET"])
def list_databases():
    """Get a list of all available databases."""
    databases = db_service.get_available_databases()
    return jsonify({
        "status": "success",
        "message": "Retrieved available databases",
        "data": {
            "databases": databases,
            "count": len(databases)
        }
    })


@bp.route("/databases/<db_id>/schema", methods=["GET"])
async def get_database_schema(db_id):
    """Get schema information for a specific database."""
    result = await db_service.get_schema(db_id)
    return jsonify(result)


@bp.route("/databases/<db_id>/extract-schema", methods=["POST"])
@jwt_required()
async def extract_database_schema(db_id):
    """Extract schema information from a database to the default database."""
    result = await db_service.extract_schema_to_default(db_id)
    return jsonify(result)


@bp.route("/databases/extract-all-schemas", methods=["POST"])
@jwt_required()
async def extract_all_database_schemas():
    """Extract schema information from all databases to the default database."""
    result = await db_service.extract_all_databases_schema()
    return jsonify(result)


@bp.route("/databases/merged-schema", methods=["GET"])
async def get_merged_schema():
    """Get merged schema information for all databases from the default database."""
    result = await db_service.get_merged_schema_from_default()
    return jsonify(result)


@bp.route("/databases/select", methods=["POST"])
async def select_database():
    """Select a database for operations."""
    data = request.get_json()
    if not data or not data.get("db_id"):
        return jsonify({
            "status": "error",
            "message": "No database ID provided"
        }), 400
        
    db_id = data.get("db_id")
    result = await db_service.select_database(db_id)
    return jsonify(result)


@bp.route("/databases/selected", methods=["GET"])
async def get_selected_database():
    """Get the currently selected database."""
    # This will be tracked in user session in a full implementation
    # For now, return the default database
    result = await db_service.select_database("default")
    return jsonify(result) 