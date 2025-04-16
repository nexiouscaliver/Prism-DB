"""
Database Tool for PrismDB agents.

This module provides tools for agents to execute SQL queries against databases
and interact with database connections.
"""
from typing import Dict, Any, List, Optional
import json

from agents.tools.base import BaseTool
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import structlog

logger = structlog.get_logger()


class DatabaseTool(BaseTool):
    """Tool for executing SQL queries against databases."""
    
    name = "database_tool"
    description = "Execute SQL queries against databases and retrieve results"
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize the DatabaseTool.
        
        Args:
            connection_string: Optional database connection string. If not provided,
                will attempt to get from the agent context.
        """
        super().__init__()
        self.connection_string = connection_string
        self.engine = None
        
    def _lazy_init_engine(self, connection_string: Optional[str] = None) -> None:
        """Initialize database engine if not already initialized.
        
        Args:
            connection_string: Optional connection string to use.
        
        Raises:
            ValueError: If no connection string is available.
        """
        conn_str = connection_string or self.connection_string
        if not conn_str:
            raise ValueError("No database connection string provided")
            
        if self.engine is None or conn_str != self.connection_string:
            self.connection_string = conn_str
            self.engine = create_engine(
                conn_str,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, 
                      connection_string: Optional[str] = None) -> Dict[str, Any]:
        """Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute.
            params: Optional parameters to use in the query.
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with query results.
            
        Raises:
            Exception: If query execution fails.
        """
        try:
            self._lazy_init_engine(connection_string)
            
            with self.engine.connect() as conn:
                # Execute query with parameters if provided
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # For SELECT queries, return results
                if result.returns_rows:
                    # Get column names
                    columns = result.keys()
                    
                    # Fetch all rows
                    rows = []
                    for row in result:
                        # Convert row to dictionary
                        row_dict = {}
                        for i, column in enumerate(columns):
                            # Handle different data types
                            value = row[i]
                            if hasattr(value, 'isoformat'):  # Handle datetime
                                row_dict[column] = value.isoformat()
                            else:
                                row_dict[column] = value
                        rows.append(row_dict)
                    
                    return {
                        "status": "success",
                        "columns": list(columns),
                        "rows": rows,
                        "row_count": len(rows)
                    }
                # For non-SELECT queries, return row count
                else:
                    return {
                        "status": "success",
                        "affected_rows": result.rowcount
                    }
                    
        except SQLAlchemyError as e:
            logger.error("Database query error", error=str(e), query=query)
            return {
                "status": "error",
                "message": str(e),
                "query": query
            }
        except Exception as e:
            logger.error("Unexpected database error", error=str(e), query=query)
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "query": query
            }
            
    def get_table_schema(self, table_name: str, connection_string: Optional[str] = None) -> Dict[str, Any]:
        """Get schema information for a table.
        
        Args:
            table_name: Name of the table to get schema for.
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with table schema information.
        """
        # Dialect-specific query to get table information
        # This example is for PostgreSQL
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position;
        """
        
        return self.execute_query(query, {"table_name": table_name}, connection_string)
    
    def list_tables(self, connection_string: Optional[str] = None) -> Dict[str, Any]:
        """List all tables in the database.
        
        Args:
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with list of tables.
        """
        # Dialect-specific query to list tables
        # This example is for PostgreSQL
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        
        return self.execute_query(query, connection_string=connection_string)
        
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Run the database tool with the provided arguments.
        
        Args:
            **kwargs: Arguments for the tool.
            
        Returns:
            Tool execution results.
        """
        action = kwargs.get("action", "execute_query")
        
        if action == "execute_query":
            query = kwargs.get("query")
            params = kwargs.get("params")
            connection_string = kwargs.get("connection_string", self.connection_string)
            
            if not query:
                return {"status": "error", "message": "No query provided"}
                
            return self.execute_query(query, params, connection_string)
            
        elif action == "get_table_schema":
            table_name = kwargs.get("table_name")
            connection_string = kwargs.get("connection_string", self.connection_string)
            
            if not table_name:
                return {"status": "error", "message": "No table name provided"}
                
            return self.get_table_schema(table_name, connection_string)
            
        elif action == "list_tables":
            connection_string = kwargs.get("connection_string", self.connection_string)
            return self.list_tables(connection_string)
            
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}",
                "valid_actions": ["execute_query", "get_table_schema", "list_tables"]
            } 