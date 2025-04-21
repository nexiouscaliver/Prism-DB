"""
Knowledge-Enabled SQL Agent using Agno.

This module implements a SQL agent with knowledge capabilities using Agno.
The agent can:
1. Load schema information, query examples, and SQL patterns into its knowledge base
2. Retrieve relevant information from the knowledge base when generating SQL
3. Learn from past queries to improve future SQL generation
"""
from typing import Dict, Any, List, Optional, Union, Tuple
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.sql import SQLTools
from agno.knowledge import AgentKnowledge
from agno.knowledge.text import TextKnowledgeBase
from agno.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KnowledgeEnabledSQLAgent:
    """SQL agent with knowledge capabilities using Agno."""
    
    def __init__(
        self,
        connection_string: str,
        knowledge_db_url: str = "postgresql://postgres:postgres@localhost:5432/agno_knowledge",
        model_id: str = "gpt-4-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.2
    ):
        """Initialize the knowledge-enabled SQL agent.
        
        Args:
            connection_string: Database connection string for the target database
            knowledge_db_url: Database URL for the knowledge base (PgVector)
            model_id: Model ID for generation
            api_key: API key for the model
            temperature: Temperature for generation
        """
        self.connection_string = connection_string
        self.model_id = model_id
        
        # Initialize model
        model = OpenAIChat(
            id=model_id,
            temperature=temperature,
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
        
        # Initialize vector database for knowledge
        vectordb = PgVector(
            uri=knowledge_db_url,
            table_name="sql_knowledge",
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small")
        )
        
        # Initialize knowledge base
        self.knowledge = TextKnowledgeBase(
            documents=[],  # Will be populated later
            vector_db=vectordb,
            chunk_size=2000,
            chunk_overlap=200
        )
        
        # Initialize SQL tools
        sql_tools = SQLTools(db_url=connection_string)
        
        # Initialize Agno agent with knowledge
        self.agent = Agent(
            name="SQL Knowledge Agent",
            model=model,
            tools=[sql_tools],
            knowledge=self.knowledge,
            instructions=[
                "Convert natural language questions to SQL queries",
                "Use the knowledge base to retrieve relevant SQL patterns and examples",
                "Reference schema information when constructing queries",
                "Ensure SQL is secure and optimized",
                "Explain the SQL generation process"
            ],
            markdown=True,
            show_tool_calls=True
        )
        
        # Track queries and results for learning
        self.query_history = []
    
    async def load_schema_knowledge(self) -> None:
        """Load database schema information into the knowledge base."""
        try:
            # Get schema using SQL tools
            sql_tools = SQLTools(db_url=self.connection_string)
            schema_info = await sql_tools.run(query="SELECT table_name, column_name, data_type FROM information_schema.columns ORDER BY table_name, ordinal_position")
            
            if not schema_info:
                logger.warning("No schema information available")
                return
                
            # Process schema info into formatted text
            if isinstance(schema_info, str):
                # Parse JSON string if needed
                try:
                    schema_data = json.loads(schema_info)
                except json.JSONDecodeError:
                    schema_data = {"data": [], "columns": []}
            else:
                schema_data = schema_info
            
            tables = {}
            for row in schema_data.get("data", []):
                table_name = row[0]
                column_name = row[1]
                data_type = row[2]
                
                if table_name not in tables:
                    tables[table_name] = []
                    
                tables[table_name].append(f"{column_name} ({data_type})")
            
            # Format schema as documents
            schema_documents = []
            for table_name, columns in tables.items():
                schema_text = f"Table: {table_name}\n"
                schema_text += "Columns:\n"
                schema_text += "\n".join([f"- {col}" for col in columns])
                schema_text += "\n\n"
                
                schema_documents.append({
                    "id": f"schema_{table_name}",
                    "text": schema_text,
                    "metadata": {
                        "type": "schema",
                        "table": table_name
                    }
                })
            
            # Add relationships information if available
            try:
                relationships_query = """
                SELECT
                    tc.table_name AS from_table,
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM
                    information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE
                    tc.constraint_type = 'FOREIGN KEY'
                """
                
                relationships_info = await sql_tools.run(query=relationships_query)
                
                if relationships_info:
                    if isinstance(relationships_info, str):
                        try:
                            relationships_data = json.loads(relationships_info)
                        except json.JSONDecodeError:
                            relationships_data = {"data": [], "columns": []}
                    else:
                        relationships_data = relationships_info
                    
                    rel_text = "Database Relationships:\n"
                    for row in relationships_data.get("data", []):
                        rel_text += f"- {row[0]}.{row[1]} -> {row[2]}.{row[3]}\n"
                    
                    schema_documents.append({
                        "id": "schema_relationships",
                        "text": rel_text,
                        "metadata": {
                            "type": "relationships"
                        }
                    })
            except Exception as e:
                logger.error(f"Error getting relationships: {str(e)}")
            
            # Add schema documents to knowledge base
            self.knowledge.add_documents(schema_documents)
            logger.info(f"Added {len(schema_documents)} schema documents to knowledge base")
            
        except Exception as e:
            logger.error(f"Error loading schema knowledge: {str(e)}")
    
    async def load_query_examples(self, examples: List[Dict[str, str]]) -> None:
        """Load SQL query examples into the knowledge base.
        
        Args:
            examples: List of dictionaries with 'question' and 'sql' keys
        """
        try:
            example_documents = []
            
            for i, example in enumerate(examples):
                question = example.get("question", "")
                sql = example.get("sql", "")
                
                if not question or not sql:
                    continue
                    
                example_text = f"Question: {question}\nSQL: {sql}\n\n"
                example_documents.append({
                    "id": f"example_{i}",
                    "text": example_text,
                    "metadata": {
                        "type": "example",
                        "question": question
                    }
                })
            
            # Add example documents to knowledge base
            self.knowledge.add_documents(example_documents)
            logger.info(f"Added {len(example_documents)} example documents to knowledge base")
            
        except Exception as e:
            logger.error(f"Error loading query examples: {str(e)}")
    
    async def load_sql_patterns(self, patterns: List[Dict[str, str]]) -> None:
        """Load SQL patterns into the knowledge base.
        
        Args:
            patterns: List of dictionaries with 'name', 'description', and 'pattern' keys
        """
        try:
            pattern_documents = []
            
            for i, pattern in enumerate(patterns):
                name = pattern.get("name", "")
                description = pattern.get("description", "")
                sql_pattern = pattern.get("pattern", "")
                
                if not name or not sql_pattern:
                    continue
                    
                pattern_text = f"Pattern: {name}\nDescription: {description}\nSQL Pattern: {sql_pattern}\n\n"
                pattern_documents.append({
                    "id": f"pattern_{i}",
                    "text": pattern_text,
                    "metadata": {
                        "type": "pattern",
                        "name": name
                    }
                })
            
            # Add pattern documents to knowledge base
            self.knowledge.add_documents(pattern_documents)
            logger.info(f"Added {len(pattern_documents)} pattern documents to knowledge base")
            
        except Exception as e:
            logger.error(f"Error loading SQL patterns: {str(e)}")
    
    async def generate_sql(self, question: str) -> Dict[str, Any]:
        """Generate SQL from a natural language question using knowledge.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with generated SQL and metadata
        """
        try:
            # Track start time
            start_time = datetime.now()
            
            # Form the prompt with knowledge retrieval context
            prompt = f"""
            Generate SQL for the following question:
            
            {question}
            
            Use your knowledge base to find relevant schema information, examples, and patterns.
            Return only the SQL query inside a code block. After the code block, provide a brief explanation.
            """
            
            # Generate SQL with the agent
            response = await self.agent.generate(prompt)
            
            # Extract SQL from response
            sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL)
            sql = sql_match.group(1).strip() if sql_match else None
            
            if not sql:
                return {
                    "status": "error",
                    "message": "Could not extract SQL from response",
                    "original_question": question,
                    "response": response
                }
            
            # Track end time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Save to query history for learning
            query_record = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "sql": sql,
                "response": response,
                "processing_time": processing_time
            }
            self.query_history.append(query_record)
            
            # Add successful query to knowledge base for future learning
            self.knowledge.add_documents([{
                "id": f"history_{query_record['id']}",
                "text": f"Question: {question}\nSQL: {sql}\n\n",
                "metadata": {
                    "type": "history",
                    "question": question,
                    "timestamp": query_record["timestamp"]
                }
            }])
            
            return {
                "status": "success",
                "sql": sql,
                "original_question": question,
                "full_response": response,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return {
                "status": "error",
                "message": f"Error generating SQL: {str(e)}",
                "original_question": question
            }
    
    async def execute_query(self, sql: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a SQL query.
        
        Args:
            sql: SQL query to execute
            params: Optional query parameters
            
        Returns:
            Query result
        """
        try:
            # Use SQL tools to execute the query
            sql_tools = SQLTools(db_url=self.connection_string)
            result = await sql_tools.run(query=sql, parameters=params)
            
            return {
                "status": "success",
                "data": result,
                "message": "Query executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                "status": "error",
                "message": f"Error executing query: {str(e)}"
            }
    
    async def process(self, question: str) -> Dict[str, Any]:
        """Process a question by generating and executing SQL.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with SQL, results, and metadata
        """
        try:
            # Generate SQL
            generation_result = await self.generate_sql(question)
            
            if generation_result.get("status") == "error":
                return generation_result
                
            sql = generation_result.get("sql")
            
            # Execute the query if possible
            execution_result = await self.execute_query(sql)
            
            # Combine results
            return {
                "status": "success",
                "original_question": question,
                "sql": sql,
                "sql_generation": generation_result,
                "query_execution": execution_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing question: {str(e)}",
                "original_question": question
            }


# Example usage
async def main():
    # Initialize the knowledge-enabled SQL agent
    agent = KnowledgeEnabledSQLAgent(
        connection_string="postgresql://postgres:postgres@localhost:5432/demo",
        knowledge_db_url="postgresql://postgres:postgres@localhost:5432/agno_knowledge",
        model_id="gpt-4-turbo"
    )
    
    # Load schema information
    await agent.load_schema_knowledge()
    
    # Load example queries
    example_queries = [
        {
            "question": "What are the top 5 customers by order total?",
            "sql": "SELECT c.customer_id, c.first_name, c.last_name, SUM(p.amount) as total_amount FROM customer c JOIN payment p ON c.customer_id = p.customer_id GROUP BY c.customer_id ORDER BY total_amount DESC LIMIT 5"
        },
        {
            "question": "How many rentals were made in each month of 2020?",
            "sql": "SELECT EXTRACT(MONTH FROM rental_date) as month, COUNT(*) as rental_count FROM rental WHERE EXTRACT(YEAR FROM rental_date) = 2020 GROUP BY month ORDER BY month"
        }
    ]
    await agent.load_query_examples(example_queries)
    
    # Load SQL patterns
    sql_patterns = [
        {
            "name": "Top N by Aggregate",
            "description": "Pattern for finding top N records by an aggregated value",
            "pattern": "SELECT [dimension_columns], [aggregate_function]([value_column]) as [alias] FROM [table] GROUP BY [dimension_columns] ORDER BY [alias] DESC LIMIT [N]"
        },
        {
            "name": "Time-based Aggregation",
            "description": "Pattern for aggregating data by time periods",
            "pattern": "SELECT EXTRACT([time_unit] FROM [date_column]) as [time_alias], [aggregate_function]([value_column]) as [value_alias] FROM [table] WHERE [date_column] BETWEEN [start_date] AND [end_date] GROUP BY [time_alias] ORDER BY [time_alias]"
        }
    ]
    await agent.load_sql_patterns(sql_patterns)
    
    # Process a question
    result = await agent.process("Which films have been rented the most times?")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 