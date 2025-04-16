"""
Agent Orchestration Engine for PrismDB.

This module handles the coordination and execution of multiple agents
to process natural language queries into SQL statements.
"""
import asyncio
from asyncio import gather
from typing import Dict, Any, List, Optional
from datetime import datetime

from celery import Celery, Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from agents.nlu_agent import NLUAgent
from agents.schema_agent import SchemaAgent
from agents.query_agent import QueryAgent
from agents.viz_agent import VizAgent as VisualizationAgent
from app.config import REDIS_URL


# Pydantic models for the orchestrator
class SQLGenerationInput(BaseModel):
    """Input parameters for SQL generation process."""
    
    query: str = Field(..., description="Natural language query to convert to SQL")
    prism_id: str = Field(..., description="Prism (database) identifier to query against")
    user_id: str = Field(..., description="User ID for tracking and permissions")
    max_tokens: int = Field(2048, description="Maximum tokens for the SQL generation")
    
    @validator('query')
    def query_not_empty(cls, v):
        """Validate that query is not empty."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class NLUResult(BaseModel):
    """Result of NLU processing."""
    
    intent: str = Field(..., description="Detected query intent")
    entities: List[Dict[str, Any]] = Field(..., description="Extracted entities")
    confidence: float = Field(..., description="Confidence score of intent detection")


class SchemaResult(BaseModel):
    """Result of schema processing."""
    
    tables: List[Dict[str, Any]] = Field(..., description="Tables in the database schema")
    relationships: List[Dict[str, Any]] = Field(..., description="Relationships between tables")


class SQLResult(BaseModel):
    """Result of SQL generation."""
    
    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the SQL query")
    confidence: float = Field(..., description="Confidence score of SQL generation")


class VisualizationResult(BaseModel):
    """Result of visualization processing."""
    
    chart_type: str = Field(..., description="Type of chart generated")
    chart_data: Dict[str, Any] = Field(..., description="Data for the chart")
    chart_options: Dict[str, Any] = Field(..., description="Chart configuration options")


class AgentResponse(BaseModel):
    """Standardized response format for orchestrator."""
    
    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Status of the request (success, error, processing)")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if status is error")
    processing_time: float = Field(..., description="Processing time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of creation")


# Configure Celery
celery_app = Celery('prismdb_tasks')
celery_logger = get_task_logger(__name__)

# Default Celery configuration
celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_soft_time_limit=60,  # 60 seconds soft time limit
    task_time_limit=120,      # 120 seconds hard time limit
    task_acks_late=True,      # Tasks are acknowledged after execution
    worker_prefetch_multiplier=1,  # Prefetch one task at a time
    task_track_started=True,  # Track when tasks are started
)


class BaseTask(Task):
    """Base Celery task with error handling and retries."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 5}
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure."""
        celery_logger.error(
            f"Task {task_id} failed: {str(exc)}",
            exc_info=exc
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)


# Celery tasks for agent execution
@celery_app.task(base=BaseTask, bind=True, name='tasks.nlu_processing')
def nlu_processing_task(self, query: str, user_id: str) -> Dict[str, Any]:
    """Process natural language query through NLU agent."""
    try:
        # Create NLU agent and process query
        nlu_agent = NLUAgent()
        result = nlu_agent.process(query, {"user_id": user_id})
        
        return result
    except SoftTimeLimitExceeded:
        celery_logger.error(f"NLU processing timed out for query: {query}")
        raise
    except Exception as e:
        celery_logger.error(f"NLU processing failed: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name='tasks.schema_processing')
def schema_processing_task(self, prism_id: str, user_id: str) -> Dict[str, Any]:
    """Process schema information for a prism."""
    try:
        # Create Schema agent and process query
        schema_agent = SchemaAgent()
        result = schema_agent.process(f"Get schema for prism {prism_id}", 
                                     {"prism_id": prism_id, "user_id": user_id})
        
        return result
    except SoftTimeLimitExceeded:
        celery_logger.error(f"Schema processing timed out for prism: {prism_id}")
        raise
    except Exception as e:
        celery_logger.error(f"Schema processing failed: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name='tasks.query_generation')
def query_generation_task(self, intent: Dict[str, Any], schema: Dict[str, Any], 
                          query: str, max_tokens: int) -> Dict[str, Any]:
    """Generate SQL query based on intent and schema."""
    try:
        # Create Query agent and generate SQL
        query_agent = QueryAgent()
        result = query_agent.process(query, {
            "intent": intent,
            "schema": schema,
            "max_tokens": max_tokens
        })
        
        return result
    except SoftTimeLimitExceeded:
        celery_logger.error(f"Query generation timed out for query: {query}")
        raise
    except Exception as e:
        celery_logger.error(f"Query generation failed: {str(e)}")
        raise


@celery_app.task(base=BaseTask, bind=True, name='tasks.visualization_generation')
def visualization_generation_task(self, sql_result: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Generate visualization based on SQL results."""
    try:
        # Create Visualization agent and generate charts
        viz_agent = VisualizationAgent()
        result = viz_agent.process(query, {
            "sql_result": sql_result,
            "query": query
        })
        
        return result
    except SoftTimeLimitExceeded:
        celery_logger.error(f"Visualization generation timed out for query: {query}")
        raise
    except Exception as e:
        celery_logger.error(f"Visualization generation failed: {str(e)}")
        raise


class Orchestrator:
    """Orchestrator for PrismDB agents.
    
    This class coordinates the execution of multiple agents to process
    natural language queries into SQL statements.
    """
    
    def __init__(self):
        """Initialize the orchestrator with agent instances."""
        self.nlu_agent = NLUAgent()
        self.schema_agent = SchemaAgent()
        self.query_agent = QueryAgent()
        self.viz_agent = VisualizationAgent()
        self.celery = celery_app
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def process_query(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a natural language query.
        
        Args:
            input_text: Natural language query.
            context: Additional context.
            
        Returns:
            Query results.
        """
        # Extract the target database ID from context if present
        db_id = "default"
        if context and "db_id" in context:
            db_id = context["db_id"]
        
        # Check if this is a multi-database query
        is_multi_db = False
        if any(keyword in input_text.lower() for keyword in ["all databases", "every database", "across databases"]):
            is_multi_db = True
            return await self.process_multi_db_query(input_text, context)
        
        # Process the query
        nlu_result = await self._run_nlu_agent(input_text, context.get("user_id") if context else None)
        
        # If NLU detected an error, return it
        if nlu_result.get("status") == "error":
            return nlu_result
        
        # Get the intent and entities from NLU
        intent = nlu_result.get("data", {}).get("intent", {})
        entities = nlu_result.get("data", {}).get("entities", [])
        
        # Get schema information for the database
        schema_result = await self._run_schema_agent(db_id, context.get("user_id") if context else None)
        
        # If schema retrieval failed, return error
        if schema_result.get("status") == "error":
            return schema_result
        
        # Pass intent, entities, and schema to query agent
        query_input = {
            "intent": intent,
            "entities": entities,
            "schema": schema_result.get("data", {}),
            "query": input_text,
            "db_id": db_id
        }
        
        # Run query agent to generate SQL
        sql_result = await self._run_query_agent(query_input)
        
        # If SQL generation failed, return error
        if sql_result.get("status") == "error":
            return sql_result
        
        # Execute the SQL query on the specified database
        sql_query = sql_result.get("data", {}).get("sql")
        if not sql_query:
            return {
                "status": "error",
                "message": "Failed to generate SQL query from natural language input"
            }
        
        # Get parameters for the query
        params = sql_result.get("data", {}).get("parameters", {})
        
        # Execute the query on the database
        query_result = await self.query_agent.execute_query(sql_query, params, db_id=db_id)
        
        # Prepare visualization if needed
        if query_result.get("status") == "success" and "rows" in query_result:
            viz_result = await self._run_visualization_agent({
                "sql_result": query_result,
                "query": input_text
            })
            
            # Add visualization to query result if successful
            if viz_result.get("status") == "success":
                query_result["visualization"] = viz_result.get("data", {})
        
        return query_result

    async def process_multi_db_query(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a natural language query across multiple databases.
        
        Args:
            input_text: Natural language query.
            context: Additional context.
            
        Returns:
            Query results from multiple databases.
        """
        # Process the query through NLU agent
        nlu_result = await self._run_nlu_agent(input_text, context.get("user_id") if context else None)
        
        # If NLU detected an error, return it
        if nlu_result.get("status") == "error":
            return nlu_result
        
        # Get the intent and entities from NLU
        intent = nlu_result.get("data", {}).get("intent", {})
        entities = nlu_result.get("data", {}).get("entities", [])
        
        # Get available databases
        available_dbs = self.query_agent.get_available_databases()
        
        # Get schema information for all available databases
        schema_results = {}
        for db_info in available_dbs:
            db_id = db_info.get("id")
            schema_result = await self._run_schema_agent(db_id, context.get("user_id") if context else None)
            if schema_result.get("status") == "success":
                schema_results[db_id] = schema_result.get("data", {})
        
        # If no schema information was retrieved, return error
        if not schema_results:
            return {
                "status": "error",
                "message": "Failed to retrieve schema information for any database"
            }
        
        # First approach: generate a single SQL query that can run on most databases
        # Pass intent, entities, and schema to query agent
        query_input = {
            "intent": intent,
            "entities": entities,
            "schema": schema_results.get("default", next(iter(schema_results.values()))),
            "query": input_text,
            "multi_db": True
        }
        
        # Run query agent to generate SQL
        sql_result = await self._run_query_agent(query_input)
        
        # If SQL generation failed, return error
        if sql_result.get("status") == "error":
            return sql_result
        
        # Execute the SQL query across all databases
        sql_query = sql_result.get("data", {}).get("sql")
        if not sql_query:
            return {
                "status": "error",
                "message": "Failed to generate SQL query from natural language input"
            }
        
        # Get parameters for the query
        params = sql_result.get("data", {}).get("parameters", {})
        
        # Execute the query across all compatible databases
        query_results = await self.query_agent.execute_query_across_all(sql_query, params)
        
        # Prepare a combined result
        combined_result = {
            "status": "success",
            "message": f"Query executed across {len(query_results.get('results', {}))} databases",
            "databases": available_dbs,
            "results": query_results.get("results", {}),
            "sql_query": sql_query,
            "parameters": params
        }
        
        return combined_result
    
    async def _run_nlu_agent(self, query: str, user_id: str) -> Dict[str, Any]:
        """Run NLU agent to detect intent and entities.
        
        In real implementation, this would use the Celery task for production.
        For testing and development, we can run it directly.
        
        Args:
            query: Natural language query
            user_id: User ID
            
        Returns:
            Dictionary with NLU processing results
        """
        # For production
        # result = nlu_processing_task.delay(query, user_id)
        # return await self._wait_for_task(result)
        
        # For development/testing, run directly
        result = await asyncio.to_thread(
            self.nlu_agent.process,
            query,
            {"user_id": user_id}
        )
        return result
    
    async def _run_schema_agent(self, prism_id: str, user_id: str) -> Dict[str, Any]:
        """Run Schema agent to get schema information.
        
        Args:
            prism_id: Prism (database) identifier
            user_id: User ID
            
        Returns:
            Dictionary with schema information
        """
        # For production
        # result = schema_processing_task.delay(prism_id, user_id)
        # return await self._wait_for_task(result)
        
        # For development/testing, run directly
        result = await asyncio.to_thread(
            self.schema_agent.process,
            f"Get schema for prism {prism_id}",
            {"prism_id": prism_id, "user_id": user_id}
        )
        return result
    
    async def _run_query_agent(self, query_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run Query agent to generate SQL.
        
        Args:
            query_input: Input dictionary for query generation
            
        Returns:
            Dictionary with SQL generation results
        """
        # For production
        # result = query_generation_task.delay(query_input["intent"], query_input["schema"], query_input["query"], query_input["max_tokens"])
        # return await self._wait_for_task(result)
        
        # For development/testing, run directly
        result = await asyncio.to_thread(
            self.query_agent.process,
            query_input["query"],
            {
                "intent": query_input["intent"],
                "schema": query_input["schema"],
                "max_tokens": query_input["max_tokens"],
                "db_id": query_input["db_id"]
            }
        )
        return result
    
    async def _run_visualization_agent(self, sql_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run visualization agent to generate charts from SQL results.
        
        Args:
            sql_result: Result from the SQL generation
            
        Returns:
            Dictionary with visualization agent results
        """
        try:
            # Run the visualization agent directly
            viz_result = self.viz_agent.process(sql_result["query"], {
                "sql_result": sql_result,
                "query": sql_result["query"]
            })
            
            return viz_result
        except Exception as e:
            # If visualization fails, we just log it and return an error
            # This prevents it from breaking the main query flow
            return {
                "status": "error",
                "message": f"Visualization generation failed: {str(e)}",
                "data": None
            }
    
    async def _wait_for_task(self, async_result) -> Dict[str, Any]:
        """Wait for a Celery task to complete.
        
        Args:
            async_result: Celery AsyncResult object
            
        Returns:
            Task result
        """
        # Check every 0.1 seconds
        while not async_result.ready():
            await asyncio.sleep(0.1)
            
        if async_result.successful():
            return async_result.result
        else:
            # Re-raise the exception
            raise async_result.result 