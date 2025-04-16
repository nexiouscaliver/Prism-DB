"""
Query Agent for PrismDB.

This module handles natural language to SQL translation,
with options for multiple LLM providers and smart parameterization.
"""

import json
import logging
import re
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from sqlalchemy import create_engine, inspect, text
from tenacity import retry, stop_after_attempt, wait_exponential

from app import config
from models.response_models import ErrorCode, ErrorResponse, SQLGenerationInfo
from services.database_service import database_service
from agents.base import PrismAgent


logger = logging.getLogger(__name__)


# Templates for SQL generation
SQL_GENERATION_TEMPLATE = """
You are a SQL expert assistant that converts natural language questions into SQL queries.

Database Information:
{database_info}

User Question: {question}

Your task:
1. Analyze the question and determine the appropriate SQL query
2. Only respond with valid SQL for the specified database type
3. Focus on writing efficient, secure SQL
4. Return ONLY the SQL query without any explanations or markdown

SQL Query:
"""

SQL_PARAM_TEMPLATE = """
You are a SQL expert assistant that extracts parameters from SQL queries for safe execution.

Original SQL Query: {sql_query}

Your task:
1. Identify values in the query that should be parameterized
2. Create a parameterized version of the query
3. Return a JSON object with:
   - "parameterized_sql": The SQL with parameter placeholders
   - "parameters": An object mapping parameter names to their values

Example output:
{
  "parameterized_sql": "SELECT * FROM users WHERE age > :min_age AND status = :status",
  "parameters": {
    "min_age": 25,
    "status": "active"
  }
}

Only respond with the JSON object, no additional text.
"""


class QueryAgent(PrismAgent):
    """Agent for converting natural language to SQL and executing queries."""
    
    def __init__(self, model_id: str = "gemini-2.0-flash-exp"):
        """Initialize the QueryAgent."""
        super().__init__(
            name="QueryAgent",
            system_prompt="""You are an expert SQL query generator that helps users query databases.
            You can work with multiple databases when requested. Always verify SQL syntax.
            Never make up tables or columns. Use only the schema provided.""",
            instructions=[
                "When asked to query a specific database, use the database_id parameter",
                "For cross-database queries, specify which database each part should run on",
                "Validate SQL queries for compatibility with the target database type"
            ],
            model_id=model_id
        )
        self.llm_provider = "gemini"  # Default to Gemini
        self.temperature = 0.2  # Default temperature
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None, db_id: str = "default") -> Dict[str, Any]:
        """Execute a SQL query on a specific database.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            db_id: Database identifier.
            
        Returns:
            Query results.
        """
        return await database_service.execute_query(query, params, db_id)
    
    async def execute_query_across_all(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a SQL query across all compatible databases.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            
        Returns:
            Combined query results.
        """
        return await database_service.execute_query_across_all(query, params)
    
    def get_available_databases(self) -> List[Dict[str, Any]]:
        """Get information about all available databases.
        
        Returns:
            List of database information.
        """
        return database_service.get_available_databases()
    
    async def get_db_schema(self, db_id: str) -> Dict[str, Any]:
        """Get schema information for a specific database.
        
        Args:
            db_id: Database identifier.
            
        Returns:
            Schema information.
        """
        return await database_service.get_schema(db_id)
    
    def _clean_sql(self, sql: str) -> str:
        """
        Clean generated SQL.
        
        Args:
            sql: Generated SQL query.
            
        Returns:
            Cleaned SQL query.
        """
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*|\s*```', '', sql)
        sql = re.sub(r'```\s*|\s*```', '', sql)
        
        # Remove any explanations
        if "SELECT" in sql:
            start_idx = sql.find("SELECT")
            sql = sql[start_idx:]
        
        return sql.strip()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def _generate_sql(self, db_id: str, question: str) -> str:
        """
        Generate SQL from natural language.
        
        Args:
            db_id: Database identifier.
            question: Natural language question.
            
        Returns:
            Generated SQL query.
        """
        # Get database schema information
        schema_info = await self.get_db_schema(db_id)
        
        if schema_info.get("status") != "success":
            raise ValueError(f"Failed to get schema for database '{db_id}': {schema_info.get('message')}")
        
        # Format schema information for prompt
        db_info = self._format_db_info_for_prompt(schema_info)
        
        # Generate SQL using the model
        if self.llm_provider == "openai":
            prompt = SQL_GENERATION_TEMPLATE.format(
                database_info=db_info, 
                question=question
            )
            response = await self._call_openai_api(prompt)
        else:
            # Use the Agno agent directly
            response = await self.generate(
                f"Generate a SQL query for database '{db_id}' from this question: {question}\n\n"
                f"Database schema:\n{db_info}\n\n"
                f"Return only the SQL query with no explanations."
            )
        
        # Clean the generated SQL
        sql = self._clean_sql(response)
        
        return sql
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API directly.
        
        Args:
            prompt: The prompt to send to the API.
            
        Returns:
            The API response text.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.OPENAI_API_KEY}"
        }
        data = {
            "model": "gpt-4-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        response_json = response.json()
        return response_json["choices"][0]["message"]["content"]
    
    def _format_db_info_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """
        Format database schema information for the prompt.
        
        Args:
            schema_info: Database schema information.
            
        Returns:
            Formatted schema information as a string.
        """
        formatted_info = []
        
        db_name = schema_info.get("db_name", "Unknown Database")
        db_id = schema_info.get("db_id", "default")
        
        formatted_info.append(f"Database Name: {db_name}")
        formatted_info.append(f"Database ID: {db_id}")
        formatted_info.append("")
        
        tables = schema_info.get("tables", [])
        
        for table in tables:
            table_name = table.get("name", "Unknown Table")
            formatted_info.append(f"Table: {table_name}")
            
            columns = table.get("columns", [])
            if columns:
                formatted_info.append("Columns:")
                for col in columns:
                    # Column format will depend on the schema structure returned by the service
                    if isinstance(col, list):
                        # If columns are returned as lists, use the first items as name and type
                        name = col[0] if len(col) > 0 else "Unknown"
                        data_type = col[1] if len(col) > 1 else "Unknown"
                        formatted_info.append(f"  - {name} ({data_type})")
                    elif isinstance(col, dict):
                        # If columns are returned as dicts, use the name and type keys
                        name = col.get("name", col.get("column_name", "Unknown"))
                        data_type = col.get("type", col.get("data_type", "Unknown"))
                        nullable = "" if col.get("nullable", "YES") == "YES" else " NOT NULL"
                        primary_key = " PRIMARY KEY" if col.get("is_primary_key", False) else ""
                        formatted_info.append(f"  - {name} ({data_type}){nullable}{primary_key}")
            
            formatted_info.append("")
        
        return "\n".join(formatted_info)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def _parameterize_sql(self, sql: str) -> Dict[str, Any]:
        """
        Convert SQL query to parameterized version.
        
        Args:
            sql: SQL query to parameterize.
            
        Returns:
            Dictionary with parameterized SQL and parameters.
        """
        try:
            if self.llm_provider == "openai":
                prompt = SQL_PARAM_TEMPLATE.format(sql_query=sql)
                response = await self._call_openai_api(prompt)
            else:
                # Use the Agno agent
                response = await self.generate(
                    f"Convert this SQL query to a parameterized version:\n\n"
                    f"{sql}\n\n"
                    f"Extract parameters and return a JSON object with 'parameterized_sql' and 'parameters'."
                )
            
            # Parse the response
            try:
                # Strip any markdown or extra text
                response = re.sub(r'```json\s*|\s*```', '', response)
                
                # Extract JSON object
                json_match = re.search(r'{.*}', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0)
                
                result = json.loads(response)
                
                # Validate result structure
                if not all(key in result for key in ["parameterized_sql", "parameters"]):
                    return {
                        "parameterized_sql": sql, 
                        "parameters": {}
                    }
                
                return result
                
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Failed to parse parameterization response: {str(e)}")
                return {
                    "parameterized_sql": sql, 
                    "parameters": {}
                }
                
        except Exception as e:
            logger.error(f"Error parameterizing SQL: {str(e)}")
            return {
                "parameterized_sql": sql, 
                "parameters": {}
            }
    
    def _validate_sql(self, db_id: str, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL syntax.
        
        Args:
            db_id: Database identifier.
            sql: SQL query to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        # Basic validation
        if not sql.strip():
            return False, "SQL query is empty"
        
        # Check for common SQL injection patterns
        injection_patterns = [
            "--", 
            "/*", 
            "*/", 
            "DROP TABLE", 
            "DROP DATABASE", 
            "DELETE FROM", 
            "TRUNCATE TABLE",
            "UPDATE .* SET",
            "INSERT INTO"
        ]
        
        # For data retrieval purposes, these patterns might indicate malicious intent
        for pattern in injection_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                if not sql.upper().startswith("SELECT"):
                    return False, f"Potentially unsafe operation detected: {pattern}"
        
        # Get available databases to check if db_id is valid
        available_dbs = self.get_available_databases()
        db_ids = [db.get("id") for db in available_dbs]
        
        if db_id not in db_ids:
            return False, f"Invalid database ID: {db_id}"
        
        return True, None
    
    async def generate_sql(self, db_id: str, question: str) -> Union[SQLGenerationInfo, ErrorResponse]:
        """
        Generate SQL from natural language question.
        
        Args:
            db_id: Database identifier.
            question: Natural language question.
            
        Returns:
            SQL generation information or error response.
        """
        try:
            # Generate SQL from natural language
            sql = await self._generate_sql(db_id, question)
            
            # Validate SQL syntax
            is_valid, error_msg = self._validate_sql(db_id, sql)
            if not is_valid:
                return ErrorResponse(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=error_msg or "SQL validation failed",
                    details={"sql": sql}
                )
            
            # Parameterize the SQL for secure execution
            param_result = await self._parameterize_sql(sql)
            
            # Create result
            return SQLGenerationInfo(
                sql=param_result["parameterized_sql"],
                original_sql=sql,
                parameters=param_result["parameters"],
                db_id=db_id,
                explanation=f"Generated SQL for question: {question}"
            )
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return ErrorResponse(
                code=ErrorCode.GENERATION_ERROR,
                message=f"Failed to generate SQL: {str(e)}",
                details={"question": question, "db_id": db_id}
            )


# Create singleton instance
query_agent = QueryAgent() 