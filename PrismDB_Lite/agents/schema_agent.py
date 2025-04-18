import logging
from typing import Dict, Any, List, Optional
import json

from .base import BaseAgent
from ..database.db_manager import PostgresManager

logger = logging.getLogger("prismdb.agent.schema")

class SchemaAgent(BaseAgent):
    """
    Schema Agent analyzes database schema and provides metadata
    for other agents to use in query generation.
    """
    
    def __init__(self, name="schema_agent", config=None):
        """
        Initialize the schema agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent
        """
        super().__init__(name, config)
        self.db_manager = None
        self.schema_cache = None
        self.cache_valid = False
        
        # Check if we need to initialize db_manager on startup
        if config and config.get("connection_string"):
            self._init_db_manager(
                config.get("connection_string"),
                config.get("pool_size", 5),
                config.get("max_overflow", 10)
            )
    
    def _init_db_manager(self, connection_string, pool_size=5, max_overflow=10):
        """
        Initialize the database manager.
        
        Args:
            connection_string (str): Database connection string
            pool_size (int, optional): Size of the connection pool
            max_overflow (int, optional): Maximum number of overflow connections
        """
        self.db_manager = PostgresManager(
            connection_string=connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow
        )
        self.logger.info("Initialized database manager")
    
    async def process(self, message, context=None):
        """
        Process a message and return schema information.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: Schema information
        """
        context = context or {}
        
        # Check if we need to initialize db_manager from context
        if not self.db_manager and context.get("db_connection"):
            connection_info = context.get("db_connection", {})
            self._init_db_manager(
                connection_info.get("connection_string"),
                connection_info.get("pool_size", 5),
                connection_info.get("max_overflow", 10)
            )
        
        # If we still don't have a db_manager, return an error
        if not self.db_manager:
            return {"error": "Database connection not available"}
        
        # Get the query or command
        query = message.get("query", "")
        command = message.get("command", "")
        
        # Check if this is a specific schema command
        if command == "refresh_schema":
            self.cache_valid = False
            self.logger.info("Schema cache invalidated")
        
        # Get schema information
        try:
            schema = await self._get_schema_info()
            
            # If we have a specific query about the schema, process it
            if query:
                schema_query_result = self._process_schema_query(query, schema)
                return {
                    "schema": schema,
                    "query_result": schema_query_result,
                    "original_query": query
                }
            else:
                # Just return the schema
                return {"schema": schema}
        except Exception as e:
            self.logger.error(f"Error retrieving schema: {str(e)}")
            return {"error": f"Schema retrieval failed: {str(e)}"}
    
    async def _get_schema_info(self):
        """
        Get schema information from the database.
        
        Returns:
            dict: Schema information
        """
        # Use cached schema if available and valid
        if self.schema_cache and self.cache_valid:
            self.log_thought("Using cached schema information")
            return self.schema_cache
        
        # Get fresh schema information
        self.log_thought("Retrieving fresh schema information from database")
        schema = self.db_manager.get_schema_metadata()
        
        # Cache the schema
        self.schema_cache = schema
        self.cache_valid = True
        
        return schema
    
    def _process_schema_query(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a specific query about the schema.
        
        Args:
            query (str): The query about the schema
            schema (dict): The schema information
            
        Returns:
            dict: Result of the schema query
        """
        self.log_thought(f"Processing schema query: {query}")
        
        # Simple keyword matching for schema queries
        query_lower = query.lower()
        
        # Find relevant information based on the query
        if "table" in query_lower and "list" in query_lower:
            return {
                "type": "table_list",
                "tables": schema.get("tables", [])
            }
        elif "column" in query_lower and "list" in query_lower:
            # Extract table name from query if present
            table_name = None
            for table in schema.get("tables", []):
                if table.lower() in query_lower:
                    table_name = table
                    break
            
            if table_name and table_name in schema.get("columns", {}):
                return {
                    "type": "column_list",
                    "table": table_name,
                    "columns": [col.get("name") for col in schema["columns"][table_name]]
                }
            else:
                return {
                    "type": "all_columns",
                    "tables_columns": {
                        table: [col.get("name") for col in cols]
                        for table, cols in schema.get("columns", {}).items()
                    }
                }
        elif "relationship" in query_lower or "foreign key" in query_lower:
            # Extract table name from query if present
            table_name = None
            for table in schema.get("tables", []):
                if table.lower() in query_lower:
                    table_name = table
                    break
            
            if table_name and table_name in schema.get("foreign_keys", {}):
                return {
                    "type": "table_relationships",
                    "table": table_name,
                    "relationships": schema["foreign_keys"][table_name]
                }
            else:
                return {
                    "type": "all_relationships",
                    "relationships": schema.get("foreign_keys", {})
                }
        elif "primary key" in query_lower:
            # Extract table name from query if present
            table_name = None
            for table in schema.get("tables", []):
                if table.lower() in query_lower:
                    table_name = table
                    break
            
            if table_name and table_name in schema.get("primary_keys", {}):
                return {
                    "type": "primary_key",
                    "table": table_name,
                    "primary_key": schema["primary_keys"][table_name]
                }
            else:
                return {
                    "type": "all_primary_keys",
                    "primary_keys": schema.get("primary_keys", {})
                }
        elif any(table.lower() in query_lower for table in schema.get("tables", [])):
            # Query is about a specific table
            table_name = next(
                (table for table in schema.get("tables", []) if table.lower() in query_lower),
                None
            )
            
            if table_name:
                return {
                    "type": "table_details",
                    "table": table_name,
                    "columns": schema.get("columns", {}).get(table_name, []),
                    "primary_key": schema.get("primary_keys", {}).get(table_name, []),
                    "foreign_keys": schema.get("foreign_keys", {}).get(table_name, [])
                }
        
        # Default to providing a summary
        return {
            "type": "schema_summary",
            "tables_count": len(schema.get("tables", [])),
            "tables": schema.get("tables", [])
        }
    
    def invalidate_cache(self):
        """
        Invalidate the schema cache.
        """
        self.cache_valid = False
        self.logger.info("Schema cache invalidated")
    
    def analyze_schema_relationships(self, schema):
        """
        Analyze schema relationships and provide additional metadata.
        
        Args:
            schema (dict): The schema information
            
        Returns:
            dict: Enhanced schema with relationship analysis
        """
        self.log_thought("Analyzing schema relationships")
        
        # Create a copy of the schema to enhance
        enhanced_schema = schema.copy()
        
        # Add join paths between tables
        join_paths = {}
        tables = schema.get("tables", [])
        
        # Build graph of table relationships
        graph = {}
        for table in tables:
            graph[table] = []
            
            # Add direct relationships based on foreign keys
            if table in schema.get("foreign_keys", {}):
                for fk in schema["foreign_keys"][table]:
                    referred_table = fk.get("referred_table")
                    if referred_table:
                        graph[table].append({
                            "table": referred_table,
                            "join": {
                                "from_cols": fk.get("constrained_columns", []),
                                "to_cols": fk.get("referred_columns", [])
                            }
                        })
        
        # Find join paths between all pairs of tables
        for source in tables:
            join_paths[source] = {}
            for target in tables:
                if source != target:
                    path = self._find_join_path(graph, source, target)
                    if path:
                        join_paths[source][target] = path
        
        enhanced_schema["join_paths"] = join_paths
        return enhanced_schema
    
    def _find_join_path(self, graph, source, target, visited=None, path=None):
        """
        Find a join path between two tables using breadth-first search.
        
        Args:
            graph (dict): Graph of table relationships
            source (str): Source table
            target (str): Target table
            visited (set, optional): Set of visited tables
            path (list, optional): Current path
            
        Returns:
            list: Join path between tables or None if no path exists
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        # Mark source as visited
        visited.add(source)
        
        # Check if we've reached the target
        if source == target:
            return path
        
        # Check neighbors
        for neighbor in graph.get(source, []):
            neighbor_table = neighbor["table"]
            if neighbor_table not in visited:
                new_path = path + [{
                    "from": source,
                    "to": neighbor_table,
                    "join": neighbor["join"]
                }]
                result = self._find_join_path(graph, neighbor_table, target, visited, new_path)
                if result:
                    return result
        
        return None 