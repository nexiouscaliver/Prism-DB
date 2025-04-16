"""
Agno SQLTools implementation for PrismDB with multi-database support.

This module provides tools for agents to execute SQL queries against multiple databases
using Agno's SQLTools as the foundation.
"""
from typing import Dict, Any, List, Optional, Union
import json

from agno.tools.sql import SQLTools
from agents.tools.base import BaseTool
import logging

from config.databases import DATABASES, DatabaseConfig

logger = logging.getLogger(__name__)


class PrismSQLTools(BaseTool):
    """Tool for executing SQL queries against multiple databases using Agno SQLTools."""
    
    name = "prism_sql_tool"
    description = "Execute SQL queries against multiple databases and retrieve results"
    
    def __init__(self):
        """Initialize the PrismSQLTools with connections to all configured databases."""
        super().__init__()
        self.sql_tools = {}
        self._initialize_connections()
        
    def _initialize_connections(self) -> None:
        """Initialize connections to all configured databases."""
        for db_config in DATABASES:
            if db_config.enabled:
                try:
                    self.sql_tools[db_config.id] = SQLTools(db_url=db_config.connection_string)
                    logger.info(f"Initialized connection to database '{db_config.name}' (ID: {db_config.id})")
                except Exception as e:
                    logger.error(f"Failed to initialize connection to database '{db_config.name}' (ID: {db_config.id}): {str(e)}")
    
    def _get_sql_tool(self, db_id: str = "default") -> Optional[SQLTools]:
        """Get the SQLTools instance for the specified database ID.
        
        Args:
            db_id: Database identifier. Defaults to "default".
            
        Returns:
            SQLTools instance or None if not found.
        """
        if db_id not in self.sql_tools:
            logger.warning(f"Database '{db_id}' not found or not initialized")
            return None
        
        return self.sql_tools[db_id]
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Run the SQL tool with the provided arguments.
        
        Args:
            **kwargs: Arguments for the tool.
            
        Returns:
            Tool execution results.
        """
        action = kwargs.get("action", "execute_query")
        db_id = kwargs.get("db_id", "default")
        
        # Get the appropriate SQL tool
        sql_tool = self._get_sql_tool(db_id)
        if not sql_tool:
            return {
                "status": "error",
                "message": f"Database '{db_id}' not found or not initialized",
                "available_databases": list(self.sql_tools.keys())
            }
        
        try:
            if action == "execute_query":
                query = kwargs.get("query")
                params = kwargs.get("params", {})
                
                if not query:
                    return {"status": "error", "message": "No query provided"}
                
                # Use Agno SQLTools to execute the query
                result = await sql_tool.run(query=query, parameters=params)
                
                # Format the response to match PrismDB's expected structure
                if isinstance(result, str):
                    try:
                        # Try to parse the result as JSON
                        parsed_result = json.loads(result)
                        return {
                            "status": "success",
                            "columns": parsed_result.get("columns", []),
                            "rows": parsed_result.get("data", []),
                            "row_count": len(parsed_result.get("data", []))
                        }
                    except json.JSONDecodeError:
                        # If not JSON, return as raw text
                        return {
                            "status": "success",
                            "result": result
                        }
                else:
                    return {
                        "status": "success",
                        "result": result
                    }
                
            elif action == "list_tables":
                # Use Agno SQLTools to list tables
                result = await sql_tool.run(query="SHOW TABLES")
                
                # Format the response
                try:
                    if isinstance(result, str):
                        parsed_result = json.loads(result)
                        return {
                            "status": "success",
                            "tables": parsed_result.get("data", [])
                        }
                    else:
                        return {
                            "status": "success",
                            "tables": result
                        }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "result": result
                    }
                
            elif action == "get_table_schema":
                table_name = kwargs.get("table_name")
                
                if not table_name:
                    return {"status": "error", "message": "No table name provided"}
                
                try:
                    # Use Agno SQLTools to get schema
                    query = f"DESC {table_name}"
                    result = await sql_tool.run(query=query)
                    
                    # Format the response
                    try:
                        if isinstance(result, str):
                            parsed_result = json.loads(result)
                            return {
                                "status": "success",
                                "schema": parsed_result.get("data", [])
                            }
                        else:
                            return {
                                "status": "success",
                                "schema": result
                            }
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing schema result for table {table_name}: {str(e)}")
                        return {
                            "status": "success",
                            "result": result
                        }
                except Exception as e:
                    logger.error(f"Error getting schema for table {table_name}: {str(e)}")
                    return {
                        "status": "error",
                        "message": f"Error getting schema: {str(e)}",
                        "table": table_name
                    }
                
            elif action == "list_databases":
                # Return the list of available databases
                return {
                    "status": "success",
                    "databases": [
                        {"id": db_id, "name": db_config.name, "type": db_config.type, "readonly": db_config.readonly}
                        for db_id, db_config in [(db, next((d for d in DATABASES if d.id == db), None)) 
                                              for db in self.sql_tools.keys()]
                        if db_config is not None
                    ]
                }
                
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}",
                    "valid_actions": ["execute_query", "list_tables", "get_table_schema", "list_databases"]
                }
                
        except Exception as e:
            logger.error(f"Error executing SQL tool action '{action}': {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "action": action,
                "db_id": db_id
            } 