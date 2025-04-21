"""
Example Natural Language to SQL agent using Agno Framework.

This module shows how to implement a natural language to SQL agent using Agno.
"""
from typing import Dict, Any, List, Optional, Union, Tuple
import asyncio
import json
import re
import logging

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.models.anthropic.claude import Claude
from agno.tools.sql import SQLTools

# Configure logging
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
5. If the query is ambiguous (e.g., "show me top 5 rows"), select an appropriate table from the schema
6. For cross-database queries, use explicit database references (db_name.table_name) in your SQL
7. If schema is empty, return "SELECT 1 as result"

SQL Query:
"""


class NLToSQLAgent:
    """Agent for converting natural language to SQL and executing queries."""
    
    def __init__(
        self, 
        connection_string: Optional[str] = None,
        model_id: str = "gpt-4-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.2
    ):
        """Initialize the NL to SQL Agent.
        
        Args:
            connection_string: Database connection string
            model_id: Model ID to use for generation
            api_key: API key for the model provider
            temperature: Temperature for generation
        """
        # Initialize the model based on ID
        if model_id.startswith("gpt-"):
            model = OpenAIChat(
                id=model_id,
                temperature=temperature,
                api_key=api_key
            )
        elif model_id.startswith("claude-"):
            model = Claude(
                id=model_id,
                temperature=temperature,
                api_key=api_key
            )
        else:  # Default to Gemini models
            model = Gemini(
                id=model_id,
                api_key=api_key,
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
        
        # Initialize Agno agent 
        self.agent = Agent(
            name="SQL Generator",
            model=model,
            instructions=[
                "Convert natural language questions to SQL queries",
                "Always check schema information before writing SQL",
                "Return only valid SQL for the given database",
                "Handle ambiguous queries gracefully",
                "Ensure security of generated SQL by avoiding direct string concatenation"
            ],
            markdown=True
        )
        
        # Initialize SQLTools if a connection string is provided
        self.sql_tools = None
        if connection_string:
            self.sql_tools = SQLTools(db_url=connection_string)
            self.agent.add_tool(self.sql_tools)
            self._load_schema()
    
    def _load_schema(self) -> None:
        """Load database schema information."""
        try:
            if not self.sql_tools:
                logger.warning("Cannot load schema: No SQL tools available")
                return
                
            # Get schema info using SQL tools
            schema_info = self.sql_tools.get_schema()
            
            # Add schema to agent memory
            if schema_info:
                for table in schema_info.get("tables", []):
                    table_name = table["name"]
                    columns = ", ".join([f"{col['name']} ({col['type']})" for col in table["columns"]])
                    table_info = f"Table {table_name}: {columns}"
                    self.agent.add_memory(table_info)
                    
                relations = schema_info.get("relationships", [])
                for relation in relations:
                    rel_info = f"Relation: {relation['from_table']}.{relation['from_column']} -> {relation['to_table']}.{relation['to_column']}"
                    self.agent.add_memory(rel_info)
                    
                logger.info(f"Loaded schema with {len(schema_info['tables'])} tables")
            else:
                logger.warning("No schema information available")
                
        except Exception as e:
            logger.error(f"Error loading schema: {str(e)}")
    
    def _format_db_info(self, schema: Dict[str, Any]) -> str:
        """Format database schema info for the prompt.
        
        Args:
            schema: Database schema information
            
        Returns:
            Formatted schema string
        """
        if not schema or not schema.get("tables"):
            return "Schema information not available."
            
        formatted = ["DATABASE SCHEMA:"]
        
        # Format tables
        for table in schema.get("tables", []):
            table_name = table["name"]
            columns = [f"{col['name']} ({col['type']})" + 
                     (" PRIMARY KEY" if col.get("is_primary", False) else "") 
                     for col in table.get("columns", [])]
            
            formatted.append(f"Table: {table_name}")
            formatted.append("Columns:")
            for col in columns:
                formatted.append(f"  - {col}")
            formatted.append("")
            
        # Format relationships
        if schema.get("relationships"):
            formatted.append("Relationships:")
            for rel in schema.get("relationships", []):
                formatted.append(f"  - {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
                
        return "\n".join(formatted)
    
    async def generate_sql(self, question: str, schema: Optional[Dict[str, Any]] = None) -> str:
        """Generate SQL from natural language.
        
        Args:
            question: Natural language question
            schema: Optional schema information
            
        Returns:
            Generated SQL query
        """
        # Format database info
        db_info = self._format_db_info(schema) if schema else "Schema information not available."
        
        # Format the prompt
        prompt = SQL_GENERATION_TEMPLATE.format(
            database_info=db_info,
            question=question
        )
        
        # Generate SQL with the agent
        response = await self.agent.generate(prompt)
        
        # Clean up the response
        sql = self._clean_sql(response)
        
        return sql
    
    def _clean_sql(self, sql: str) -> str:
        """Clean up the generated SQL by removing markdown and unnecessary text.
        
        Args:
            sql: Raw SQL response
            
        Returns:
            Cleaned SQL
        """
        # Remove markdown code blocks if present
        if "```sql" in sql or "```" in sql:
            pattern = r"```(?:sql)?(.*?)```"
            matches = re.findall(pattern, sql, re.DOTALL)
            if matches:
                sql = matches[0].strip()
        
        # Remove explanations or additional text before/after SQL
        if "SELECT" in sql.upper():
            select_pos = sql.upper().find("SELECT")
            sql = sql[select_pos:]
            
        # Remove comments
        sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
        
        return sql.strip()
    
    async def execute_query(self, sql: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a SQL query.
        
        Args:
            sql: SQL query to execute
            params: Optional query parameters
            
        Returns:
            Query result
        """
        if not self.sql_tools:
            return {
                "status": "error",
                "message": "No database connection available"
            }
            
        try:
            result = await self.sql_tools.run(query=sql, parameters=params)
            
            if not result:
                return {
                    "status": "success", 
                    "message": "Query executed but returned no results",
                    "data": []
                }
                
            return {
                "status": "success",
                "message": "Query executed successfully",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Query execution failed: {str(e)}"
            }
    
    async def process(self, question: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a natural language question to SQL and execute it.
        
        Args:
            question: Natural language question
            schema: Optional database schema
            
        Returns:
            Dictionary with SQL and results
        """
        try:
            # Generate SQL
            sql = await self.generate_sql(question, schema)
            
            # Execute the query
            if self.sql_tools:
                result = await self.execute_query(sql)
                
                return {
                    "status": "success",
                    "sql": sql,
                    "original_question": question,
                    "result": result
                }
            else:
                # Just return the SQL if no database connection
                return {
                    "status": "success",
                    "sql": sql,
                    "original_question": question
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing question: {str(e)}",
                "original_question": question
            }


# Example usage
async def main():
    # Initialize agent with a connection string
    agent = NLToSQLAgent(connection_string="sqlite:///example.db")
    
    # Process a question
    result = await agent.process("Show me the top 5 customers by order total")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 