"""
SchemaAgent for PrismDB.

This agent is responsible for providing schema information for database contexts.
It retrieves table structures, relationships, and other metadata needed for SQL generation.
"""
from typing import Dict, Any, List, Optional
import os
from sqlalchemy import create_engine, inspect, MetaData, Table, text
from sqlalchemy.exc import SQLAlchemyError
from agents.base import PrismAgent
from config.databases import get_db_config, get_all_db_configs

def get_database_connection(database_name: str):
    """Establish a connection to the specified database.
    
    Args:
        database_name: Name of the database to connect to
        
    Returns:
        SQLAlchemy engine or None if connection fails
    """
    try:
        # Get the database configuration by ID
        db_config = get_db_config(database_name)
        if not db_config:
            # Fall back to the default PostgreSQL connection if the specific DB isn't found
            default_db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prismdb")
            engine = create_engine(default_db_url)
            return engine
            
        # Create SQLAlchemy engine for the database
        engine = create_engine(db_config.connection_string)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

class SchemaAgent(PrismAgent):
    """Agent for retrieving and analyzing database schema information.
    
    This agent is responsible for providing contextual information about
    database schemas, including tables, columns, relationships, and constraints.
    This information is used by the QueryAgent to generate accurate SQL.
    """
    
    def __init__(self):
        """Initialize the SchemaAgent with appropriate tools and instructions."""
        super().__init__(
            name="SchemaAgent",
            system_prompt="""You are a SchemaAgent responsible for analyzing database schemas
            and providing contextual information about tables, columns, relationships, and constraints.
            Your job is to provide accurate schema information that can be used to generate SQL queries.""",
            instructions=[
                "Analyze database schema structures accurately",
                "Detect table relationships and foreign keys",
                "Identify primary keys and constraints",
                "Provide detailed column information including data types",
                "Format all responses as JSON with consistent structure"
            ]
        )
        
    def process(self, database_name: str, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process a schema extraction request and return the database schema.
        
        Args:
            database_name: Name of the database to extract schema from
            table_names: Optional list of specific tables to extract
            
        Returns:
            Dictionary with the database schema information
        """
        try:
            if not database_name:
                return {
                    "status": "error",
                    "message": "No database name provided",
                    "errors": [{"type": "missing_parameter", "message": "Database name is required"}]
                }
            
            # Get connection to the database
            engine = get_database_connection(database_name)
            if not engine:
                return {
                    "status": "error",
                    "message": f"Failed to connect to database '{database_name}'",
                    "errors": [{"type": "connection_error", "message": f"Could not establish connection to {database_name}"}]
                }
            
            # Extract schema information
            schema_info = self._extract_schema(engine, database_name, table_names)
            
            # Return dictionary directly instead of using success_response
            return {
                "status": "success",
                "message": f"Successfully extracted schema for '{database_name}'",
                "data": schema_info
            }
            
        except Exception as e:
            # Return dictionary directly instead of using error_response
            return {
                "status": "error",
                "message": f"Schema extraction failed: {str(e)}",
                "errors": [{"type": "schema_extraction_error", "message": str(e)}]
            } 

    def _extract_schema(self, engine, database_name: str, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract database schema information.
        
        Args:
            engine: SQLAlchemy engine object
            database_name: Name of the database
            table_names: Optional list of specific tables to extract
            
        Returns:
            Dictionary containing schema information
        """
        schema_info = {
            "database_name": database_name,
            "tables": [],
            "relationships": []
        }
        
        try:
            # Use SQLAlchemy inspector to get table information
            inspector = inspect(engine)
            
            if table_names:
                # Filter to specific tables if provided
                tables_to_process = [t for t in table_names if t.strip()]
            else:
                # Get all tables
                tables_to_process = inspector.get_table_names()
            
            # Process each table
            for table_name in tables_to_process:
                table_info = {"name": table_name, "columns": []}
                
                # Get column information
                columns = inspector.get_columns(table_name)
                for col in columns:
                    column = {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "is_primary": False,  # Will set this in the next step
                        "nullable": col.get("nullable", True),
                    }
                    if col.get("default") is not None:
                        column["default"] = str(col.get("default"))
                    table_info["columns"].append(column)
                
                # Get primary key information
                pk_constraint = inspector.get_pk_constraint(table_name)
                pk_columns = pk_constraint.get('constrained_columns', [])
                
                # Mark primary key columns
                for column in table_info["columns"]:
                    if column["name"] in pk_columns:
                        column["is_primary"] = True
                
                schema_info["tables"].append(table_info)
                
                # Get foreign key information
                fk_constraints = inspector.get_foreign_keys(table_name)
                for fk in fk_constraints:
                    for i, from_col in enumerate(fk['constrained_columns']):
                        to_col = fk['referred_columns'][i] if i < len(fk['referred_columns']) else fk['referred_columns'][0]
                        relation = {
                            "from_table": table_name,
                            "from_column": from_col,
                            "to_table": fk['referred_table'],
                            "to_column": to_col,
                            "relationship_type": "many-to-one"  # Assuming most common case
                        }
                        schema_info["relationships"].append(relation)
            
            return schema_info
            
        except Exception as e:
            print(f"Error extracting schema: {e}")
            # Return at least partial schema if we have it
            return schema_info
            
    def get_available_databases(self) -> Dict[str, Any]:
        """Get information about all available databases.
        
        Returns:
            Dictionary with database information
        """
        try:
            all_dbs = get_all_db_configs()
            return {
                "status": "success",
                "message": "Retrieved available databases",
                "data": {
                    "databases": all_dbs,
                    "count": len(all_dbs)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to retrieve available databases: {str(e)}",
                "errors": [{"type": "database_listing_error", "message": str(e)}]
            } 