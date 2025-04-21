"""
Database Service for PrismDB.

This service provides a centralized interface for managing database connections
and executing SQL queries across multiple databases.
"""
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import os
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, text, select
from sqlalchemy.exc import SQLAlchemyError

from config.databases import DATABASES, DatabaseConfig, get_db_config
from agno.tools.sql import SQLTools

import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections and executing SQL queries."""
    
    def __init__(self):
        """Initialize the database service."""
        self.connections = {}
        self._initialize_connections()
        self.default_db_id = "default"
        
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
        try:
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
            
            # Validate params is a dictionary
            if params is not None and not isinstance(params, dict):
                logger.warning(f"Invalid params type: {type(params)}, using empty dict instead")
                params = {}
            
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
            except AttributeError as ae:
                logger.error(f"AttributeError executing query on database '{db_id}': {str(ae)}")
                return {
                    "status": "error",
                    "error_type": "attribute_error",
                    "message": f"AttributeError: {str(ae)}",
                    "query": query,
                    "db_id": db_id
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
        except AttributeError as ae:
            logger.error(f"AttributeError in database_service.execute_query: {str(ae)}")
            return {
                "status": "error",
                "error_type": "attribute_error",
                "message": f"AttributeError in database service: {str(ae)}",
                "query": query,
                "db_id": db_id
            }
        except Exception as e:
            logger.error(f"Unexpected error in database_service.execute_query: {str(e)}")
            return {
                "status": "error",
                "error_type": "unexpected_error",
                "message": f"Unexpected error: {str(e)}",
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
        try:
            results = {}
            tasks = []
            
            # Validate params is a dictionary
            if params is not None and not isinstance(params, dict):
                logger.warning(f"Invalid params type: {type(params)}, using empty dict instead")
                params = {}
                
            for db_id, connection in self.connections.items():
                # Skip read-only databases for non-SELECT queries
                if connection["config"].readonly and not query.strip().upper().startswith("SELECT"):
                    continue
                
                # Create task for executing query
                task = asyncio.create_task(self.execute_query(query, params, db_id))
                tasks.append((db_id, task))
            
            # Wait for all tasks to complete
            for db_id, task in tasks:
                try:
                    results[db_id] = await task
                except Exception as e:
                    logger.error(f"Error awaiting task for database '{db_id}': {str(e)}")
                    results[db_id] = {
                        "status": "error",
                        "error_type": "task_error",
                        "message": f"Error: {str(e)}",
                        "query": query,
                        "db_id": db_id
                    }
            
            return {
                "status": "success",
                "results": results
            }
        except AttributeError as ae:
            logger.error(f"AttributeError in database_service.execute_query_across_all: {str(ae)}")
            return {
                "status": "error",
                "error_type": "attribute_error",
                "message": f"AttributeError in database service: {str(ae)}",
                "query": query
            }
        except Exception as e:
            logger.error(f"Unexpected error in database_service.execute_query_across_all: {str(e)}")
            return {
                "status": "error",
                "error_type": "unexpected_error",
                "message": f"Unexpected error: {str(e)}",
                "query": query
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
            db_id: Database identifier. If "default" and default DB has no tables, returns schemas from all databases.
            
        Returns:
            Schema information.
        """
        logger.info(f"Fetching schema for database ID: {db_id}")
        
        if db_id not in self.connections:
            available_dbs = list(self.connections.keys())
            logger.error(f"Database '{db_id}' not found. Available databases: {available_dbs}")
            return {
                "status": "error",
                "message": f"Database '{db_id}' not found or not initialized",
                "available_databases": available_dbs
            }
            
        try:
            connection = self.connections[db_id]
            logger.info(f"Retrieving schema for database '{db_id}' ({connection['config'].name})")
            
            # Use SQLAlchemy to get schema information
            engine = create_engine(connection["config"].connection_string)
            inspector = inspect(engine)
            
            # Get list of tables
            tables = []
            table_names = inspector.get_table_names()
            logger.info(f"Found {len(table_names)} tables in database '{db_id}'")
            
            for table_name in table_names:
                columns = []
                
                # Get column information
                for column in inspector.get_columns(table_name):
                    columns.append({
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column.get("nullable", True),
                        "default": str(column.get("default")) if column.get("default") else None
                    })
                
                # Get primary key information
                pk_constraint = inspector.get_pk_constraint(table_name)
                pk_columns = pk_constraint.get('constrained_columns', [])
                
                # Get foreign key information
                fk_constraints = inspector.get_foreign_keys(table_name)
                foreign_keys = []
                
                for fk in fk_constraints:
                    foreign_keys.append({
                        "columns": fk.get("constrained_columns", []),
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns", [])
                    })
                
                tables.append({
                    "name": table_name,
                    "columns": columns,
                    "primary_key_columns": pk_columns,
                    "foreign_keys": foreign_keys
                })
            
            # If this is the default database and it has no tables, try to get schemas from all databases
            if db_id == "default" and len(tables) == 0:
                logger.info("Default database has no tables, fetching schemas from all available databases")
                all_tables = []
                for other_db_id, other_conn in self.connections.items():
                    if other_db_id != "default":
                        try:
                            logger.info(f"Fetching schema from alternative database: {other_db_id}")
                            other_schema = await self.get_schema(other_db_id)
                            if other_schema["status"] == "success" and "data" in other_schema and "tables" in other_schema["data"]:
                                # Prefix table names with database ID to avoid collisions
                                for table in other_schema["data"]["tables"]:
                                    # Add database origin information
                                    table["db_id"] = other_db_id
                                    table["db_name"] = other_conn["config"].name
                                all_tables.extend(other_schema["data"]["tables"])
                        except Exception as inner_e:
                            logger.warning(f"Error fetching schema from {other_db_id}: {str(inner_e)}")
                
                if all_tables:
                    logger.info(f"Successfully found {len(all_tables)} tables across all databases")
                    tables = all_tables
            
            logger.info(f"Returning schema with {len(tables)} tables for database '{db_id}'")
            return {
                "status": "success",
                "message": f"Schema retrieved for database '{db_id}'",
                "data": {
                    "tables": tables,
                    "database_id": db_id,
                    "database_name": connection["config"].name,
                    "database_type": connection["config"].type
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting schema for database '{db_id}': {str(e)}")
            import traceback
            logger.error(f"Schema retrieval traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error getting schema: {str(e)}",
                "database_id": db_id
            }
            
    async def extract_schema_to_default(self, source_db_id: str) -> Dict[str, Any]:
        """Extract schema information from a source database and store it in the default database.
        
        Args:
            source_db_id: Source database identifier.
            
        Returns:
            Status of the operation.
        """
        if source_db_id not in self.connections:
            return {
                "status": "error",
                "message": f"Source database '{source_db_id}' not found or not initialized",
                "available_databases": list(self.connections.keys())
            }
            
        if self.default_db_id not in self.connections:
            return {
                "status": "error",
                "message": f"Default database '{self.default_db_id}' not found or not initialized"
            }
            
        try:
            # Get schema information from source database
            schema_result = await self.get_schema(source_db_id)
            
            if schema_result["status"] != "success":
                return {
                    "status": "error",
                    "message": f"Failed to get schema from source database: {schema_result['message']}"
                }
                
            schema_data = schema_result["data"]
            
            # Create schema tables in default database if they don't exist
            await self._ensure_schema_tables_exist()
            
            # Store database metadata
            db_metadata = {
                "id": source_db_id,
                "name": schema_data["database_name"],
                "type": schema_data["database_type"]
            }
            
            # Store database in metadata table
            await self.execute_query(
                """
                INSERT INTO database_metadata (db_id, db_name, db_type, created_at)
                VALUES (:db_id, :db_name, :db_type, NOW())
                ON CONFLICT (db_id) DO UPDATE SET
                    db_name = :db_name,
                    db_type = :db_type,
                    updated_at = NOW()
                """,
                {
                    "db_id": db_metadata["id"],
                    "db_name": db_metadata["name"],
                    "db_type": db_metadata["type"]
                },
                self.default_db_id
            )
            
            # Store table metadata
            for table in schema_data["tables"]:
                # Store table metadata
                await self.execute_query(
                    """
                    INSERT INTO table_metadata (db_id, table_name, created_at)
                    VALUES (:db_id, :table_name, NOW())
                    ON CONFLICT (db_id, table_name) DO UPDATE SET
                        updated_at = NOW()
                    """,
                    {
                        "db_id": source_db_id,
                        "table_name": table["name"]
                    },
                    self.default_db_id
                )
                
                # Store column metadata
                for column in table["columns"]:
                    await self.execute_query(
                        """
                        INSERT INTO column_metadata (db_id, table_name, column_name, data_type, is_nullable, column_default, created_at)
                        VALUES (:db_id, :table_name, :column_name, :data_type, :is_nullable, :column_default, NOW())
                        ON CONFLICT (db_id, table_name, column_name) DO UPDATE SET
                            data_type = :data_type,
                            is_nullable = :is_nullable,
                            column_default = :column_default,
                            updated_at = NOW()
                        """,
                        {
                            "db_id": source_db_id,
                            "table_name": table["name"],
                            "column_name": column["name"],
                            "data_type": column["type"],
                            "is_nullable": column["nullable"],
                            "column_default": column["default"]
                        },
                        self.default_db_id
                    )
                
                # Store primary key metadata
                for pk_column in table["primary_key_columns"]:
                    await self.execute_query(
                        """
                        INSERT INTO primary_key_metadata (db_id, table_name, column_name, created_at)
                        VALUES (:db_id, :table_name, :column_name, NOW())
                        ON CONFLICT (db_id, table_name, column_name) DO UPDATE SET
                            updated_at = NOW()
                        """,
                        {
                            "db_id": source_db_id,
                            "table_name": table["name"],
                            "column_name": pk_column
                        },
                        self.default_db_id
                    )
                
                # Store foreign key metadata
                for fk in table["foreign_keys"]:
                    for i, column in enumerate(fk["columns"]):
                        referenced_column = fk["referred_columns"][i] if i < len(fk["referred_columns"]) else fk["referred_columns"][0]
                        await self.execute_query(
                            """
                            INSERT INTO foreign_key_metadata (
                                db_id, table_name, column_name, 
                                referenced_table, referenced_column, created_at
                            )
                            VALUES (
                                :db_id, :table_name, :column_name, 
                                :referenced_table, :referenced_column, NOW()
                            )
                            ON CONFLICT (db_id, table_name, column_name, referenced_table, referenced_column) DO UPDATE SET
                                updated_at = NOW()
                            """,
                            {
                                "db_id": source_db_id,
                                "table_name": table["name"],
                                "column_name": column,
                                "referenced_table": fk["referred_table"],
                                "referenced_column": referenced_column
                            },
                            self.default_db_id
                        )
            
            return {
                "status": "success",
                "message": f"Successfully extracted schema from '{source_db_id}' to default database",
                "data": {
                    "source_db": source_db_id,
                    "table_count": len(schema_data["tables"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting schema from '{source_db_id}' to default database: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting schema: {str(e)}",
                "source_db": source_db_id
            }
    
    async def _ensure_schema_tables_exist(self) -> None:
        """Ensure that the schema metadata tables exist in the default database."""
        try:
            # Create database_metadata table
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS database_metadata (
                    db_id VARCHAR(50) PRIMARY KEY,
                    db_name VARCHAR(100) NOT NULL,
                    db_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP
                )
                """,
                {},
                self.default_db_id
            )
            
            # Create table_metadata table
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS table_metadata (
                    id SERIAL PRIMARY KEY,
                    db_id VARCHAR(50) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    CONSTRAINT table_metadata_unique UNIQUE (db_id, table_name),
                    FOREIGN KEY (db_id) REFERENCES database_metadata(db_id)
                )
                """,
                {},
                self.default_db_id
            )
            
            # Create column_metadata table
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS column_metadata (
                    id SERIAL PRIMARY KEY,
                    db_id VARCHAR(50) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    column_name VARCHAR(100) NOT NULL,
                    data_type VARCHAR(100) NOT NULL,
                    is_nullable BOOLEAN NOT NULL,
                    column_default TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    CONSTRAINT column_metadata_unique UNIQUE (db_id, table_name, column_name),
                    FOREIGN KEY (db_id, table_name) REFERENCES table_metadata(db_id, table_name)
                )
                """,
                {},
                self.default_db_id
            )
            
            # Create primary_key_metadata table
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS primary_key_metadata (
                    id SERIAL PRIMARY KEY,
                    db_id VARCHAR(50) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    column_name VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    CONSTRAINT pk_metadata_unique UNIQUE (db_id, table_name, column_name),
                    FOREIGN KEY (db_id, table_name, column_name) REFERENCES column_metadata(db_id, table_name, column_name)
                )
                """,
                {},
                self.default_db_id
            )
            
            # Create foreign_key_metadata table
            await self.execute_query(
                """
                CREATE TABLE IF NOT EXISTS foreign_key_metadata (
                    id SERIAL PRIMARY KEY,
                    db_id VARCHAR(50) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    column_name VARCHAR(100) NOT NULL,
                    referenced_table VARCHAR(100) NOT NULL,
                    referenced_column VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP,
                    CONSTRAINT fk_metadata_unique UNIQUE (db_id, table_name, column_name, referenced_table, referenced_column),
                    FOREIGN KEY (db_id, table_name, column_name) REFERENCES column_metadata(db_id, table_name, column_name)
                )
                """,
                {},
                self.default_db_id
            )
        except Exception as e:
            logger.error(f"Error ensuring schema tables exist: {str(e)}")
            raise
            
    async def extract_all_databases_schema(self) -> Dict[str, Any]:
        """Extract schema information from all databases to the default database.
        
        Returns:
            Status of the operation.
        """
        try:
            results = {}
            
            for db_id in self.connections:
                if db_id != self.default_db_id:
                    result = await self.extract_schema_to_default(db_id)
                    results[db_id] = result
            
            return {
                "status": "success",
                "message": "Schema extraction completed",
                "results": results
            }
        except Exception as e:
            logger.error(f"Error extracting all database schemas: {str(e)}")
            return {
                "status": "error",
                "message": f"Error extracting all schemas: {str(e)}"
            }
            
    async def get_merged_schema_from_default(self) -> Dict[str, Any]:
        """Get merged schema information for all databases from the default database.
        
        Returns:
            Merged schema information.
        """
        try:
            # Get list of databases
            db_result = await self.execute_query(
                "SELECT db_id, db_name, db_type FROM database_metadata",
                {},
                self.default_db_id
            )
            
            if db_result["status"] != "success":
                return {
                    "status": "error",
                    "message": "Failed to get database metadata"
                }
            
            databases = db_result["rows"]
            schema = {"databases": []}
            
            for db in databases:
                db_schema = {
                    "id": db["db_id"],
                    "name": db["db_name"],
                    "type": db["db_type"],
                    "tables": []
                }
                
                # Get tables for this database
                tables_result = await self.execute_query(
                    "SELECT table_name FROM table_metadata WHERE db_id = :db_id",
                    {"db_id": db["db_id"]},
                    self.default_db_id
                )
                
                if tables_result["status"] == "success":
                    for table in tables_result["rows"]:
                        table_schema = {
                            "name": table["table_name"],
                            "columns": [],
                            "primary_keys": [],
                            "foreign_keys": []
                        }
                        
                        # Get columns for this table
                        columns_result = await self.execute_query(
                            """
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM column_metadata
                            WHERE db_id = :db_id AND table_name = :table_name
                            """,
                            {"db_id": db["db_id"], "table_name": table["table_name"]},
                            self.default_db_id
                        )
                        
                        if columns_result["status"] == "success":
                            for column in columns_result["rows"]:
                                table_schema["columns"].append({
                                    "name": column["column_name"],
                                    "type": column["data_type"],
                                    "nullable": column["is_nullable"],
                                    "default": column["column_default"]
                                })
                                
                        # Get primary keys for this table
                        pk_result = await self.execute_query(
                            """
                            SELECT column_name
                            FROM primary_key_metadata
                            WHERE db_id = :db_id AND table_name = :table_name
                            """,
                            {"db_id": db["db_id"], "table_name": table["table_name"]},
                            self.default_db_id
                        )
                        
                        if pk_result["status"] == "success":
                            for pk in pk_result["rows"]:
                                table_schema["primary_keys"].append(pk["column_name"])
                                
                        # Get foreign keys for this table
                        fk_result = await self.execute_query(
                            """
                            SELECT column_name, referenced_table, referenced_column
                            FROM foreign_key_metadata
                            WHERE db_id = :db_id AND table_name = :table_name
                            """,
                            {"db_id": db["db_id"], "table_name": table["table_name"]},
                            self.default_db_id
                        )
                        
                        if fk_result["status"] == "success":
                            for fk in fk_result["rows"]:
                                table_schema["foreign_keys"].append({
                                    "column": fk["column_name"],
                                    "referenced_table": fk["referenced_table"],
                                    "referenced_column": fk["referenced_column"]
                                })
                                
                        db_schema["tables"].append(table_schema)
                        
                schema["databases"].append(db_schema)
                
            return {
                "status": "success",
                "message": "Merged schema retrieved successfully",
                "data": schema
            }
            
        except Exception as e:
            logger.error(f"Error getting merged schema: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting merged schema: {str(e)}"
            }
    
    async def select_database(self, db_id: str) -> Dict[str, Any]:
        """Select a database for operations.
        
        Args:
            db_id: Database identifier.
            
        Returns:
            Status of the operation.
        """
        if db_id not in self.connections:
            return {
                "status": "error",
                "message": f"Database '{db_id}' not found or not initialized",
                "available_databases": list(self.connections.keys())
            }
            
        try:
            database = self.connections[db_id]
            
            return {
                "status": "success",
                "message": f"Selected database '{db_id}'",
                "data": {
                    "db_id": db_id,
                    "name": database["config"].name,
                    "type": database["config"].type,
                    "readonly": database["config"].readonly
                }
            }
        except Exception as e:
            logger.error(f"Error selecting database '{db_id}': {str(e)}")
            return {
                "status": "error",
                "message": f"Error selecting database: {str(e)}",
                "db_id": db_id
            }


# Create singleton instance
database_service = DatabaseService() 