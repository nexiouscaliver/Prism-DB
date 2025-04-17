"""
Schema Tool for PrismDB agents.

This module provides tools for agents to retrieve, understand, and map database schemas.
"""
from typing import Dict, Any, List, Optional, Union
import json

from agents.tools.base import BaseTool
from ai.tools.base import ToolResponseFormatter
from sqlalchemy import create_engine, inspect, MetaData, Table, Column
from sqlalchemy.exc import SQLAlchemyError

import structlog

logger = structlog.get_logger()


class SchemaTool(BaseTool):
    """Tool for retrieving and understanding database schemas."""
    
    name = "schema_tool"
    description = "Retrieve, analyze, and map database schemas"
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize the SchemaTool.
        
        Args:
            connection_string: Optional database connection string. If not provided,
                will attempt to get from the agent context.
        """
        super().__init__()
        self.connection_string = connection_string
        self.engine = None
        self.inspector = None
        self.metadata = None
        self.formatter = ToolResponseFormatter()
        
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
                pool_size=2,
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True
            )
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()
    
    def get_table_schema(self, table_name: str, connection_string: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed schema information for a table.
        
        Args:
            table_name: Name of the table to get schema for.
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with detailed table schema information.
        """
        try:
            self._lazy_init_engine(connection_string)
            
            # Get columns info
            columns = self.inspector.get_columns(table_name)
            
            # Get primary key info
            pk_columns = self.inspector.get_pk_constraint(table_name).get('constrained_columns', [])
            
            # Get foreign key info
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            # Get index info
            indexes = self.inspector.get_indexes(table_name)
            
            # Format the response
            formatted_columns = []
            for col in columns:
                column_info = {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": col.get("default"),
                    "is_primary_key": col["name"] in pk_columns
                }
                formatted_columns.append(column_info)
                
            formatted_foreign_keys = []
            for fk in foreign_keys:
                fk_info = {
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                    "name": fk.get("name")
                }
                formatted_foreign_keys.append(fk_info)
                
            formatted_indexes = []
            for idx in indexes:
                idx_info = {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx["unique"]
                }
                formatted_indexes.append(idx_info)
                
            return self.formatter.format_success_response(
                message="Schema retrieved successfully",
                data={
                    "table_name": table_name,
                    "columns": formatted_columns,
                    "primary_key_columns": pk_columns,
                    "foreign_keys": formatted_foreign_keys,
                    "indexes": formatted_indexes
                }
            )
                    
        except SQLAlchemyError as e:
            logger.error("Schema retrieval error", error=str(e), table=table_name)
            return self.formatter.format_error_response(
                message=f"Error retrieving schema for table '{table_name}'",
                errors=[{"type": "SQLAlchemyError", "message": str(e)}]
            )
        except Exception as e:
            logger.error("Unexpected schema error", error=str(e), table=table_name)
            return self.formatter.format_error_response(
                message=f"Unexpected error retrieving schema for table '{table_name}'",
                errors=[{"type": type(e).__name__, "message": str(e)}]
            )
    
    def list_tables(self, connection_string: Optional[str] = None) -> Dict[str, Any]:
        """List all tables in the database with basic information.
        
        Args:
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with list of tables and basic information.
        """
        try:
            self._lazy_init_engine(connection_string)
            
            # Get all table names
            table_names = self.inspector.get_table_names()
            
            # Get basic info for each table
            tables_info = []
            for table_name in table_names:
                # Get column count
                columns = self.inspector.get_columns(table_name)
                
                # Get primary key info
                pk_columns = self.inspector.get_pk_constraint(table_name).get('constrained_columns', [])
                
                # Check for foreign keys
                foreign_keys = self.inspector.get_foreign_keys(table_name)
                
                tables_info.append({
                    "name": table_name,
                    "column_count": len(columns),
                    "has_primary_key": len(pk_columns) > 0,
                    "has_foreign_keys": len(foreign_keys) > 0
                })
                
            return self.formatter.format_success_response(
                message="Tables listed successfully",
                data={
                    "tables": tables_info,
                    "table_count": len(tables_info)
                }
            )
                    
        except SQLAlchemyError as e:
            logger.error("Table listing error", error=str(e))
            return self.formatter.format_error_response(
                message="Error listing tables",
                errors=[{"type": "SQLAlchemyError", "message": str(e)}]
            )
        except Exception as e:
            logger.error("Unexpected error listing tables", error=str(e))
            return self.formatter.format_error_response(
                message="Unexpected error listing tables",
                errors=[{"type": type(e).__name__, "message": str(e)}]
            )
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the schema tool with the provided arguments.
        
        Args:
            **kwargs: Tool execution arguments.
                - action: The action to perform (get_table_schema, list_tables, get_schema_diagram, etc.)
                - table_name: The name of the table (for get_table_schema)
                - connection_string: Optional connection string to override the default.
                
        Returns:
            Tool execution results.
        """
        action = kwargs.get("action")
        connection_string = kwargs.get("connection_string") or self.connection_string
        
        if action == "get_table_schema":
            table_name = kwargs.get("table_name")
            if not table_name:
                return self.formatter.format_error_response(
                    message="No table name provided",
                    errors=[{"type": "ValidationError", "message": "table_name is required for get_table_schema action"}]
                )
            return self.get_table_schema(table_name, connection_string)
            
        elif action == "list_tables":
            return self.list_tables(connection_string)
            
        elif action == "get_schema_diagram":
            # TODO: Implement schema diagram generation
            return self.formatter.format_error_response(
                message="get_schema_diagram action not implemented yet"
            )
            
        else:
            return self.formatter.format_error_response(
                message=f"Unknown action: {action}",
                errors=[{"type": "ValidationError", "message": "Valid actions are: get_table_schema, list_tables, get_schema_diagram"}]
            ) 