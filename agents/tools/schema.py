"""
Schema Tool for PrismDB agents.

This module provides tools for agents to retrieve, understand, and map database schemas.
"""
from typing import Dict, Any, List, Optional, Union
import json

from agents.tools.base import BaseTool
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
                
            return {
                "status": "success",
                "table_name": table_name,
                "columns": formatted_columns,
                "primary_key_columns": pk_columns,
                "foreign_keys": formatted_foreign_keys,
                "indexes": formatted_indexes
            }
                    
        except SQLAlchemyError as e:
            logger.error("Schema retrieval error", error=str(e), table=table_name)
            return {
                "status": "error",
                "message": str(e),
                "table": table_name
            }
        except Exception as e:
            logger.error("Unexpected schema error", error=str(e), table=table_name)
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "table": table_name
            }
    
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
                
            return {
                "status": "success",
                "tables": tables_info,
                "table_count": len(tables_info)
            }
                    
        except SQLAlchemyError as e:
            logger.error("Table listing error", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error("Unexpected error listing tables", error=str(e))
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def get_schema_diagram(self, connection_string: Optional[str] = None) -> Dict[str, Any]:
        """Generate a textual schema diagram showing relationships between tables.
        
        Args:
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with schema diagram information.
        """
        try:
            self._lazy_init_engine(connection_string)
            
            # Get all table names
            table_names = self.inspector.get_table_names()
            
            # Collect relationship information
            relationships = []
            tables_info = {}
            
            for table_name in table_names:
                # Get columns for each table
                columns = []
                for col in self.inspector.get_columns(table_name):
                    pk_constraint = self.inspector.get_pk_constraint(table_name)
                    pk_cols = pk_constraint.get('constrained_columns', [])
                    
                    column_type = str(col['type'])
                    is_pk = col['name'] in pk_cols
                    
                    columns.append({
                        "name": col['name'],
                        "type": column_type,
                        "is_primary_key": is_pk,
                        "nullable": col.get('nullable', True)
                    })
                
                tables_info[table_name] = {
                    "columns": columns
                }
                
                # Get foreign key relationships
                foreign_keys = self.inspector.get_foreign_keys(table_name)
                for fk in foreign_keys:
                    for i, col in enumerate(fk['constrained_columns']):
                        relationships.append({
                            "from_table": table_name,
                            "from_column": col,
                            "to_table": fk['referred_table'],
                            "to_column": fk['referred_columns'][i]
                        })
            
            # Generate diagram representation
            diagram = {
                "tables": tables_info,
                "relationships": relationships
            }
            
            return {
                "status": "success",
                "diagram": diagram
            }
                    
        except SQLAlchemyError as e:
            logger.error("Schema diagram generation error", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error("Unexpected error generating schema diagram", error=str(e))
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def map_user_terms(self, user_terms: List[str], connection_string: Optional[str] = None) -> Dict[str, Any]:
        """Map natural language terms to database schema elements.
        
        Args:
            user_terms: List of terms to map to schema elements.
            connection_string: Optional connection string to override the default.
            
        Returns:
            Dictionary with mappings of terms to schema elements.
        """
        try:
            self._lazy_init_engine(connection_string)
            
            # Get all table names
            table_names = self.inspector.get_table_names()
            
            # Collect all column names from all tables
            all_columns = {}
            for table_name in table_names:
                columns = self.inspector.get_columns(table_name)
                all_columns[table_name] = [col['name'] for col in columns]
            
            # Simple mapping logic - in production, this would use more
            # sophisticated NLP and semantic matching techniques
            mappings = {}
            for term in user_terms:
                # Convert term to lowercase for case-insensitive matching
                term_lower = term.lower()
                
                # Check for table name matches
                table_matches = []
                for table in table_names:
                    if term_lower in table.lower():
                        table_matches.append(table)
                
                # Check for column name matches
                column_matches = []
                for table, columns in all_columns.items():
                    for column in columns:
                        if term_lower in column.lower():
                            column_matches.append({"table": table, "column": column})
                
                mappings[term] = {
                    "table_matches": table_matches,
                    "column_matches": column_matches
                }
            
            return {
                "status": "success",
                "mappings": mappings
            }
                    
        except SQLAlchemyError as e:
            logger.error("Term mapping error", error=str(e))
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error("Unexpected error mapping terms", error=str(e))
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Run the schema tool with the provided arguments.
        
        Args:
            **kwargs: Arguments for the tool.
            
        Returns:
            Tool execution results.
        """
        action = kwargs.get("action", "list_tables")
        connection_string = kwargs.get("connection_string", self.connection_string)
        
        if action == "get_table_schema":
            table_name = kwargs.get("table_name")
            
            if not table_name:
                return {"status": "error", "message": "No table name provided"}
                
            return self.get_table_schema(table_name, connection_string)
            
        elif action == "list_tables":
            return self.list_tables(connection_string)
            
        elif action == "get_schema_diagram":
            return self.get_schema_diagram(connection_string)
            
        elif action == "map_user_terms":
            user_terms = kwargs.get("user_terms", [])
            
            if not user_terms:
                return {"status": "error", "message": "No user terms provided"}
                
            return self.map_user_terms(user_terms, connection_string)
            
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}",
                "valid_actions": ["get_table_schema", "list_tables", "get_schema_diagram", "map_user_terms"]
            } 