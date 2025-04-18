import logging
import json
import time
from typing import Dict, Any, List, Optional

from .base import BaseAgent
from ..database.db_manager import PostgresManager, ExecutionError

logger = logging.getLogger("prismdb.agent.execution")

class ExecutionAgent(BaseAgent):
    """
    Execution Agent safely executes SQL queries and handles timeout controls.
    """
    
    def __init__(self, name="execution_agent", config=None):
        """
        Initialize the execution agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent
        """
        super().__init__(name, config)
        self.db_manager = None
        self.default_timeout = 30  # Default timeout in seconds
        
        # Check if we need to initialize db_manager on startup
        if config and config.get("connection_string"):
            self._init_db_manager(
                config.get("connection_string"),
                config.get("pool_size", 5),
                config.get("max_overflow", 10)
            )
            
        # Set default timeout if provided in config
        if config and config.get("default_timeout"):
            self.default_timeout = config.get("default_timeout")
    
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
        Process a message and execute SQL.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: Execution result
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
        
        # Get the SQL query
        sql = message.get("sql", "")
        if not sql:
            return {"error": "No SQL query provided"}
        
        # Get timeout from message or use default
        timeout = message.get("timeout", self.default_timeout)
        
        # Get parameters if provided
        params = message.get("params", {})
        
        self.log_thought(f"Executing SQL: {sql}")
        self.log_thought(f"Timeout: {timeout} seconds")
        
        # Execute the SQL query
        try:
            start_time = time.time()
            result = self.db_manager.execute_sql(sql, timeout, params)
            execution_time = time.time() - start_time
            
            self.log_thought(f"Query executed successfully in {execution_time:.2f} seconds")
            self.log_thought(f"Result has {len(result.get('data', []))} rows")
            
            return {
                "result": result,
                "execution_time": execution_time,
                "success": True,
                "row_count": len(result.get("data", []))
            }
        except ExecutionError as e:
            self.logger.error(f"SQL execution error: {str(e)}")
            return {
                "error": f"SQL execution failed: {str(e)}",
                "success": False
            }
        except Exception as e:
            self.logger.error(f"Unexpected error during execution: {str(e)}")
            return {
                "error": f"Unexpected error: {str(e)}",
                "success": False
            }
    
    def analyze_query_performance(self, sql, execution_time):
        """
        Analyze query performance and provide optimization suggestions.
        
        Args:
            sql (str): The SQL query
            execution_time (float): Query execution time in seconds
            
        Returns:
            dict: Performance analysis
        """
        self.log_thought(f"Analyzing query performance for execution time: {execution_time:.2f}s")
        
        # Simple performance analysis based on execution time
        performance = {}
        
        if execution_time < 0.1:
            performance["rating"] = "excellent"
            performance["suggestions"] = []
        elif execution_time < 0.5:
            performance["rating"] = "good"
            performance["suggestions"] = []
        elif execution_time < 1.0:
            performance["rating"] = "acceptable"
            performance["suggestions"] = ["Consider adding indexes if this query runs frequently"]
        elif execution_time < 3.0:
            performance["rating"] = "slow"
            performance["suggestions"] = [
                "Consider adding indexes on filtered columns",
                "Check for full table scans in the query plan",
                "Consider optimizing JOIN conditions"
            ]
        else:
            performance["rating"] = "very slow"
            performance["suggestions"] = [
                "Query needs optimization",
                "Check for missing indexes",
                "Consider rewriting with more efficient joins",
                "Check for unnecessary subqueries",
                "Consider breaking down into smaller queries"
            ]
        
        # Basic SQL patterns to check
        if "SELECT *" in sql:
            performance["suggestions"].append("Avoid SELECT * - specify only needed columns")
        
        if "DISTINCT" in sql and execution_time > 0.5:
            performance["suggestions"].append("DISTINCT operations can be expensive - check if necessary")
        
        if "ORDER BY" in sql and "LIMIT" not in sql and execution_time > 0.5:
            performance["suggestions"].append("Consider adding LIMIT to ORDER BY queries")
        
        if sql.count("JOIN") > 2 and execution_time > 1.0:
            performance["suggestions"].append("Multiple JOINs detected - ensure all are necessary")
        
        return performance
    
    def execute_explain_plan(self, sql):
        """
        Execute EXPLAIN PLAN for a SQL query.
        
        Args:
            sql (str): The SQL query
            
        Returns:
            dict: Explain plan result
        """
        explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"
        
        try:
            result = self.db_manager.execute_sql(explain_sql)
            explain_plan = result.get("data", [{}])[0].get("QUERY PLAN", [])
            
            return {
                "explain_plan": explain_plan,
                "success": True
            }
        except Exception as e:
            self.logger.error(f"Error getting explain plan: {str(e)}")
            return {
                "error": f"Explain plan failed: {str(e)}",
                "success": False
            } 