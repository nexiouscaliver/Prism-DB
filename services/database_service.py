"""
Database Service for PrismDB.

This service provides a centralized interface for managing database connections
and executing SQL queries across multiple databases.
"""
from typing import Dict, Any, List, Optional, Union
import asyncio
import json

from config.databases import DATABASES, DatabaseConfig
from agno.tools.sql import SQLTools

import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections and executing SQL queries."""
    
    def __init__(self):
        """Initialize the database service."""
        self.connections = {}
        self._initialize_connections()
    
    def _initialize_connections(self) -> None:
        """Initialize connections to all configured databases."""
        for db_config in DATABASES:
            if db_config.enabled:
                try:
                    self.connections[db_config.id] = {
                        "config": db_config,
                        "tool": SQLTools(db_url=db_config.connection_string)
                    }
                    logger.info(f"Initialized connection to database '{db_config.name}' (ID: {db_config.id})")
                except Exception as e:
                    logger.error(f"Failed to initialize connection to database '{db_config.name}' (ID: {db_config.id}): {str(e)}")
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, 
                           db_id: str = "default") -> Dict[str, Any]:
        """Execute a SQL query against a specific database.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            db_id: Database identifier.
            
        Returns:
            Query results.
        """
        if db_id not in self.connections:
            return {
                "status": "error",
                "error_type": "database_not_found",
                "message": f"Database '{db_id}' not found or not initialized",
                "available_databases": list(self.connections.keys())
            }
        
        connection = self.connections[db_id]
        
        # Check if read-only and this is not a SELECT query
        if connection["config"].readonly and not query.strip().upper().startswith("SELECT"):
            return {
                "status": "error",
                "error_type": "read_only_violation",
                "message": f"Database '{db_id}' is read-only, cannot execute non-SELECT queries"
            }
        
        try:
            result = await connection["tool"].run(query=query, parameters=params or {})
            
            # Process the result to match PrismDB's expected format
            if isinstance(result, str):
                try:
                    # Try to parse as JSON
                    parsed_result = json.loads(result)
                    return {
                        "status": "success",
                        "columns": parsed_result.get("columns", []),
                        "rows": parsed_result.get("data", []),
                        "row_count": len(parsed_result.get("data", [])),
                        "db_id": db_id,
                        "db_name": connection["config"].name
                    }
                except json.JSONDecodeError:
                    # Return as plain text
                    return {
                        "status": "success",
                        "result": result,
                        "db_id": db_id,
                        "db_name": connection["config"].name
                    }
            else:
                return {
                    "status": "success",
                    "result": result,
                    "db_id": db_id,
                    "db_name": connection["config"].name
                }
        except Exception as e:
            error_msg = str(e).lower()
            error_type = "execution_error"
            
            # Try to categorize the error
            if "syntax" in error_msg:
                error_type = "syntax_error"
            elif "not found" in error_msg or "doesn't exist" in error_msg:
                error_type = "not_found_error"
            elif "duplicate" in error_msg or "unique" in error_msg:
                error_type = "unique_constraint_error"
            elif "foreign key" in error_msg:
                error_type = "foreign_key_error"
            elif "permission" in error_msg or "access" in error_msg:
                error_type = "permission_error"
            
            logger.error(f"Error executing query on database '{db_id}': {str(e)}")
            return {
                "status": "error",
                "error_type": error_type,
                "message": f"Error: {str(e)}",
                "query": query,
                "db_id": db_id
            }
    
    async def execute_query_across_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a SQL query across all enabled, compatible databases.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            
        Returns:
            Combined query results.
        """
        results = {}
        tasks = []
        
        for db_id, connection in self.connections.items():
            # Skip read-only databases for non-SELECT queries
            if connection["config"].readonly and not query.strip().upper().startswith("SELECT"):
                continue
            
            # Create task for executing query
            task = asyncio.create_task(self.execute_query(query, params, db_id))
            tasks.append((db_id, task))
        
        # Wait for all tasks to complete
        for db_id, task in tasks:
            results[db_id] = await task
        
        return {
            "status": "success",
            "results": results
        }
    
    def get_available_databases(self) -> List[Dict[str, Any]]:
        """Get information about all available databases.
        
        Returns:
            List of database information.
        """
        return [
            {
                "id": db_id,
                "name": connection["config"].name,
                "type": connection["config"].type,
                "readonly": connection["config"].readonly
            }
            for db_id, connection in self.connections.items()
        ]
    
    async def get_schema(self, db_id: str = "default") -> Dict[str, Any]:
        """Get schema information for a specific database.
        
        Args:
            db_id: Database identifier.
            
        Returns:
            Schema information.
        """
        if db_id not in self.connections:
            return {
                "status": "error",
                "message": f"Database '{db_id}' not found or not initialized",
                "available_databases": list(self.connections.keys())
            }
        
        connection = self.connections[db_id]
        db_type = connection["config"].type
        
        try:
            # Use different queries based on database type
            if db_type == "postgres":
                tables_query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """
                table_schema_query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """
            elif db_type == "mysql":
                tables_query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    ORDER BY table_name
                """
                table_schema_query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}' AND table_schema = DATABASE()
                    ORDER BY ordinal_position
                """
            elif db_type == "sqlite":
                tables_query = "SELECT name as table_name FROM sqlite_master WHERE type='table'"
                table_schema_query = "PRAGMA table_info('{table_name}')"
            else:
                # Default for other databases
                tables_query = "SHOW TABLES"
                table_schema_query = "DESC {table_name}"
            
            # Get list of tables
            tables_result = await connection["tool"].run(query=tables_query)
            
            # Parse the result
            tables = []
            table_names = []
            
            if isinstance(tables_result, str):
                try:
                    tables_result = json.loads(tables_result)
                    if "data" in tables_result and isinstance(tables_result["data"], list):
                        for row in tables_result["data"]:
                            if isinstance(row, list) and len(row) > 0:
                                table_names.append(row[0])
                            elif isinstance(row, dict) and "table_name" in row:
                                table_names.append(row["table_name"])
                except Exception as e:
                    logger.error(f"Failed to parse tables result: {str(e)}")
                    return {
                        "status": "error",
                        "message": f"Failed to parse tables result: {str(e)}"
                    }
            elif isinstance(tables_result, list):
                table_names = tables_result
            
            # Get schema for each table
            for table_name in table_names:
                query = table_schema_query.format(table_name=table_name)
                schema_result = await connection["tool"].run(query=query)
                
                columns = []
                try:
                    if isinstance(schema_result, str):
                        schema_result = json.loads(schema_result)
                        if "data" in schema_result:
                            columns = schema_result["data"]
                    else:
                        columns = schema_result
                except Exception as e:
                    logger.error(f"Failed to parse schema for {table_name}: {str(e)}")
                    continue
                
                tables.append({
                    "name": table_name,
                    "columns": columns
                })
            
            return {
                "status": "success",
                "db_id": db_id,
                "db_name": connection["config"].name,
                "db_type": db_type,
                "tables": tables
            }
        except Exception as e:
            logger.error(f"Error getting schema for database '{db_id}': {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "db_id": db_id
            }


# Create singleton instance
database_service = DatabaseService() 