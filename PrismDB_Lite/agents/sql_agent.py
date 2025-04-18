import logging
import json
import re
import google.generativeai as genai
from typing import Dict, Any, List, Optional

from .base import BaseAgent

logger = logging.getLogger("prismdb.agent.sql")

class SQLError(Exception):
    """Error that occurs when SQL generation or validation fails."""
    pass

class SQLAgent(BaseAgent):
    """
    SQL Agent generates SQL queries from natural language input,
    with validation from Google Gemini Pro.
    """
    
    def __init__(self, name="sql_agent", config=None):
        """
        Initialize the SQL agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent
        """
        super().__init__(name, config)
        self.gemini_api_key = config.get("gemini_api_key") if config else None
        
        # Initialize Gemini client if API key is available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.logger.info("Google Gemini client initialized")
        else:
            self.logger.warning("Gemini API key not found")
    
    async def process(self, message, context=None):
        """
        Process a message and generate SQL.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: Generated SQL and metadata
        """
        context = context or {}
        
        # Get the natural language query
        query = message.get("query", "")
        if not query and isinstance(message, str):
            query = message
        
        self.log_thought(f"Generating SQL for query: {query}")
        
        # Get the database schema from context
        schema = context.get("schema", {})
        
        # Get the intent and entities from context
        intent = context.get("intent", {})
        entities = context.get("entities", [])
        
        try:
            # Generate SQL based on natural language query and context
            sql = await self._generate_sql(query, schema, intent, entities)
            
            # Validate the generated SQL
            validation_result = await self._validate_sql(sql, schema)
            
            if validation_result.get("is_valid", False):
                # Return the validated SQL
                return {
                    "sql": sql,
                    "confidence": validation_result.get("confidence", 0.8),
                    "validation": validation_result
                }
            else:
                # Fix the SQL based on validation errors
                fixed_sql = await self._fix_sql(sql, validation_result, schema)
                
                # Validate the fixed SQL again
                revalidation = await self._validate_sql(fixed_sql, schema)
                
                return {
                    "sql": fixed_sql,
                    "confidence": revalidation.get("confidence", 0.6),
                    "validation": revalidation,
                    "original_sql": sql
                }
                
        except Exception as e:
            self.logger.error(f"Error generating SQL: {str(e)}")
            return {"error": f"SQL generation failed: {str(e)}"}
    
    async def _generate_sql(self, query: str, schema: Dict, intent: Dict, entities: List) -> str:
        """
        Generate SQL from natural language using Google Gemini Pro.
        
        Args:
            query (str): The natural language query
            schema (dict): Database schema information
            intent (dict): Intent classification
            entities (list): Extracted entities
        
        Returns:
            str: Generated SQL query
        """
        self.log_thought("Generating SQL with Gemini")
        
        # Construct schema information for the prompt
        schema_info = self._format_schema_for_prompt(schema)
        
        # Format entities information for the prompt
        entities_info = json.dumps(entities) if entities else "No entities extracted"
        
        # Create the prompt for Gemini
        prompt = (
            "You are an expert SQL writer. Generate a valid SQL query based on the following information:\n\n"
            f"User Query: {query}\n\n"
            f"Database Schema:\n{schema_info}\n\n"
            f"Intent: {json.dumps(intent) if intent else 'No intent provided'}\n\n"
            f"Extracted Entities: {entities_info}\n\n"
            "Rules for SQL generation:\n"
            "1. Use standard SQL syntax compatible with PostgreSQL\n"
            "2. Use appropriate joins based on the schema relationships\n"
            "3. Include comments to explain complex parts\n"
            "4. Be careful with table and column names (case-sensitive)\n"
            "5. Validate subqueries are correct\n"
            "6. Handle null values appropriately\n"
            "7. Use WITH clause for complex queries\n\n"
            "Output ONLY the SQL query, no explanations."
        )
        
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        
        # Extract SQL from the response
        result_text = response.text
        
        # Clean up the response - extract SQL from code blocks if needed
        if "```sql" in result_text:
            sql = result_text.split("```sql")[1].split("```")[0].strip()
        elif "```" in result_text:
            sql = result_text.split("```")[1].split("```")[0].strip()
        else:
            sql = result_text.strip()
        
        self.log_thought(f"Generated SQL: {sql}")
        return sql
    
    async def _validate_sql(self, sql: str, schema: Dict) -> Dict[str, Any]:
        """
        Validate the generated SQL query using Gemini.
        
        Args:
            sql (str): The SQL query to validate
            schema (dict): Database schema information
            
        Returns:
            dict: Validation result with errors and confidence
        """
        self.log_thought("Validating SQL with Gemini")
        
        # Format schema information for the prompt
        schema_info = self._format_schema_for_prompt(schema)
        
        # Create the prompt for validation
        prompt = (
            "Validate the following SQL query against the provided database schema. "
            "Check for syntax errors, schema compliance, and potential issues.\n\n"
            f"SQL Query:\n{sql}\n\n"
            f"Database Schema:\n{schema_info}\n\n"
            "Provide validation results in JSON format with the following structure:\n"
            "{\n"
            '  "is_valid": true/false,\n'
            '  "confidence": 0.95,\n'
            '  "errors": [\n'
            '    {"type": "syntax", "description": "Error description", "line": 2},\n'
            '    {"type": "schema", "description": "Table X does not exist", "line": 3}\n'
            '  ],\n'
            '  "warnings": [\n'
            '    {"type": "performance", "description": "Query might be slow", "suggestion": "Add index"}\n'
            '  ],\n'
            '  "optimization_hints": ["Use index on column X", "Consider using a JOIN instead of subquery"]\n'
            "}"
        )
        
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        
        # Extract JSON from the response
        result_text = response.text
        
        try:
            # Handle case where model might return markdown or extra text
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text.strip()
            
            validation_result = json.loads(json_str)
            
            # Log validation outcome
            if validation_result.get("is_valid", False):
                self.log_thought("SQL validation passed")
            else:
                errors = validation_result.get("errors", [])
                self.log_thought(f"SQL validation failed with {len(errors)} errors")
                for error in errors:
                    self.log_thought(f"- {error.get('type')}: {error.get('description')}")
            
            return validation_result
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse validation JSON: {str(e)}")
            return {
                "is_valid": False,
                "confidence": 0.2,
                "errors": [{"type": "validation_error", "description": "Failed to parse validation result"}]
            }
    
    async def _fix_sql(self, sql: str, validation_result: Dict, schema: Dict) -> str:
        """
        Fix SQL based on validation errors.
        
        Args:
            sql (str): The SQL query to fix
            validation_result (dict): Validation result with errors
            schema (dict): Database schema information
            
        Returns:
            str: Fixed SQL query
        """
        self.log_thought("Fixing SQL based on validation errors")
        
        # Extract errors from validation result
        errors = validation_result.get("errors", [])
        warnings = validation_result.get("warnings", [])
        
        if not errors and not warnings:
            return sql
        
        # Format errors and warnings for the prompt
        error_info = json.dumps(errors)
        warning_info = json.dumps(warnings)
        
        # Format schema information for the prompt
        schema_info = self._format_schema_for_prompt(schema)
        
        # Create the prompt for fixing the SQL
        prompt = (
            "Fix the following SQL query based on the validation errors and warnings. "
            "Make only necessary changes to fix the issues while preserving the original query intent.\n\n"
            f"Original SQL Query:\n{sql}\n\n"
            f"Validation Errors:\n{error_info}\n\n"
            f"Validation Warnings:\n{warning_info}\n\n"
            f"Database Schema:\n{schema_info}\n\n"
            "Output ONLY the fixed SQL query, no explanations."
        )
        
        model = genai.GenerativeModel('gemini-pro')
        response = await model.generate_content_async(prompt)
        
        # Extract fixed SQL from the response
        result_text = response.text
        
        # Clean up the response - extract SQL from code blocks if needed
        if "```sql" in result_text:
            fixed_sql = result_text.split("```sql")[1].split("```")[0].strip()
        elif "```" in result_text:
            fixed_sql = result_text.split("```")[1].split("```")[0].strip()
        else:
            fixed_sql = result_text.strip()
        
        self.log_thought(f"Fixed SQL: {fixed_sql}")
        return fixed_sql
    
    def _format_schema_for_prompt(self, schema: Dict) -> str:
        """
        Format schema information for prompt.
        
        Args:
            schema (dict): Database schema information
            
        Returns:
            str: Formatted schema information
        """
        if not schema:
            return "Schema information not available"
        
        formatted_schema = []
        
        # Add tables
        tables = schema.get("tables", [])
        formatted_schema.append(f"Tables: {', '.join(tables)}")
        formatted_schema.append("")
        
        # Add columns for each table
        for table in tables:
            if table in schema.get("columns", {}):
                columns = schema["columns"][table]
                formatted_schema.append(f"Table: {table}")
                column_lines = []
                for col in columns:
                    col_name = col.get("name", "")
                    col_type = col.get("type", "")
                    nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                    default = f"DEFAULT {col.get('default')}" if col.get("default") is not None else ""
                    column_lines.append(f"  - {col_name} ({col_type}) {nullable} {default}".strip())
                formatted_schema.extend(column_lines)
                
                # Add primary key
                if table in schema.get("primary_keys", {}):
                    pk = schema["primary_keys"][table]
                    if pk:
                        formatted_schema.append(f"  Primary Key: {', '.join(pk)}")
                
                # Add foreign keys
                if table in schema.get("foreign_keys", {}):
                    fks = schema["foreign_keys"][table]
                    for fk in fks:
                        constrained = fk.get("constrained_columns", [])
                        referred_table = fk.get("referred_table", "")
                        referred_cols = fk.get("referred_columns", [])
                        if constrained and referred_table and referred_cols:
                            formatted_schema.append(
                                f"  Foreign Key: {', '.join(constrained)} references {referred_table}({', '.join(referred_cols)})"
                            )
                
                formatted_schema.append("")
        
        return "\n".join(formatted_schema)
    
    def sanitize_sql(self, sql: str) -> str:
        """
        Sanitize SQL to prevent injection.
        
        Args:
            sql (str): SQL query to sanitize
            
        Returns:
            str: Sanitized SQL query
        """
        # Basic checks for dangerous patterns
        dangerous_patterns = [
            r"--",               # SQL comment
            r"/\*.*?\*/",        # Multi-line comment
            r";\s*DROP",         # DROP statement after semicolon
            r";\s*DELETE",       # DELETE statement after semicolon
            r";\s*UPDATE",       # UPDATE statement after semicolon
            r";\s*INSERT",       # INSERT statement after semicolon
            r";\s*ALTER",        # ALTER statement after semicolon
            r";\s*CREATE",       # CREATE statement after semicolon
            r"EXECUTE\s+",       # EXECUTE statement
            r"xp_cmdshell",      # SQL Server command shell
            r"sp_execute",       # SQL Server stored procedure execution
        ]
        
        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                self.logger.warning(f"Dangerous SQL pattern detected: {pattern}")
                raise SQLError(f"Potentially unsafe SQL detected with pattern: {pattern}")
        
        # Remove multiple statements (allow only one)
        if ";" in sql:
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            if len(statements) > 1:
                self.logger.warning("Multiple SQL statements detected")
                return statements[0]
        
        return sql 