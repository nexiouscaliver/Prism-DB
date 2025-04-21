"""
NLU Agent for PrismDB.

This agent is responsible for natural language understanding,
including intent classification and entity extraction.
"""
from typing import Dict, Any, List, Optional, Union
import json
import datetime
import uuid
import asyncio

from agno.models.google import Gemini
from pydantic import BaseModel, Field, validator

from agents.base import PrismAgent
from agents.tools.schema import SchemaTool
from app.config import GOOGLE_API_KEY, get_model_config


# Define Pydantic models for structured responses
class Entity(BaseModel):
    """Entity extracted from the query."""
    
    name: str = Field(..., description="Entity name")
    value: Any = Field(..., description="Entity value")
    type: str = Field(..., description="Entity type (e.g., metric, filter, date)")


class NLUResponse(BaseModel):
    """Structured response from the NLU agent."""
    
    intent: str = Field(..., description="Query intent classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for intent classification")
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities from the query")
    context_needs: List[str] = Field(default_factory=list, description="Additional context needed for query processing")
    ambiguities: List[str] = Field(default_factory=list, description="Potential ambiguities in the query")
    processed_query: str = Field(..., description="Processed and normalized query text")
    original_query: str = Field(..., description="Original query text")
    suggested_sql: Optional[str] = Field(None, description="Suggested SQL query if applicable")

    @validator('intent')
    def intent_must_be_valid(cls, v):
        """Validate that intent is one of the allowed values."""
        allowed_intents = [
            "data_retrieval", 
            "report_generation", 
            "trend_analysis",
            "comparison",
            "aggregation",
            "prediction",
            "anomaly_detection",
            "unknown"
        ]
        if v not in allowed_intents:
            raise ValueError(f"Intent must be one of: {', '.join(allowed_intents)}")
        return v


class NLUAgent(PrismAgent):
    """NLU Agent for processing natural language queries.
    
    This agent is responsible for:
    1. Intent classification - determining what the user wants to do
    2. Entity extraction - identifying key elements in the query
    3. Ambiguity detection - identifying and potentially resolving ambiguities
    4. Context analysis - determining additional context needed
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        model_id: str = "gemini-2.0-flash"
    ):
        """Initialize the NLU Agent.
        
        Args:
            connection_string: Database connection string.
            model_id: Gemini model identifier to use.
        """
        # Initialize the Gemini model
        model_config = get_model_config(model_id)
        
        model = Gemini(
            id=model_id,
            api_key=GOOGLE_API_KEY,
            generation_config={
                "temperature": model_config.get("temperature", 0.1),
                "top_p": model_config.get("top_p", 0.95),
                "top_k": model_config.get("top_k", 0),
                "max_output_tokens": model_config.get("max_output_tokens", 2048),
            }
        )
        
        # Initialize schema tool with connection string
        tools = []
        if connection_string:
            schema_tool = SchemaTool(connection_string=connection_string)
            tools.append(schema_tool)
        
        # NLU-specific instructions
        nlu_instructions = [
            "Extract all entities from the query including metrics, filters, dates, and dimensions",
            "Classify the query intent using the allowed intent categories",
            "Identify any ambiguities in the query",
            "Determine what additional context is needed to process the query",
            "Always return a structured response in the specified JSON format",
            "For complex queries, suggest SQL or break down into multiple steps"
        ]
        
        # System prompt for NLU Agent
        system_prompt = """
        You are an expert Natural Language Understanding agent specialized in converting
        database queries in natural language to structured representations.
        
        Your task is to:
        1. Accurately classify the intent of each query
        2. Extract all relevant entities and their values
        3. Identify any ambiguities that need resolution
        4. Determine what additional context might be needed
        
        You have access to database schema information and can use it to validate
        entities against actual database tables and columns.
        """
        
        # Initialize the NLU agent with the PrismAgent base class
        super().__init__(
            name="NLU Agent",
            tools=tools,
            system_prompt=system_prompt,
            instructions=nlu_instructions,
            model=model
        )
        
        self.model_id = model_id
        self.connection_string = connection_string
        self.schema_loaded = False
        
        # Load database schema if connection string is provided
        if connection_string:
            self._load_schema()
    
    def _load_schema(self) -> None:
        """Load database schema information."""
        try:
            # Find the schema tool
            schema_tool = next((tool for tool in self.tools if isinstance(tool, SchemaTool)), None)
            
            if not schema_tool:
                print("Schema tool not available")
                return
                
            # Use the schema tool to get database schema
            result = schema_tool.list_tables()
            
            if result["status"] == "success":
                tables = result["data"]["tables"]
                
                # Add schema information to agent memory
                schema_info = f"Database contains {len(tables)} tables: "
                schema_info += ", ".join([table["name"] for table in tables])
                print(f"SCHEMA INFO: {schema_info}")
                
                # For each table, get detailed schema information
                for table in tables:
                    table_name = table["name"]
                    table_schema = schema_tool.get_table_schema(table_name)
                    
                    if table_schema["status"] == "success":
                        # Format column information
                        columns_info = []
                        for col in table_schema["data"]["columns"]:
                            col_info = f"{col['name']} ({col['type']})"
                            if col["is_primary_key"]:
                                col_info += " (PK)"
                            columns_info.append(col_info)
                        
                        # Add table schema to agent memory
                        table_info = f"Table {table_name} has columns: "
                        table_info += ", ".join(columns_info)
                        print(f"TABLE SCHEMA: {table_info}")
                
                self.schema_loaded = True
            else:
                print(f"ERROR: Failed to load schema: {result.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"ERROR: Exception loading schema: {str(e)}")
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a query with the NLU model and extract structured information.
        
        Args:
            query: The natural language query to process.
            context: Optional context information.
            
        Returns:
            Structured information extracted from the query.
        """
        if not query or not query.strip():
            return {"intent": "unknown", "confidence": 0.0, "entities": []}
        
        try:
            # Format context as JSON string if provided
            context_str = json.dumps(context) if context else "{}"
            
            # Get database schema information if available
            schema_info = ""
            db_id = context.get("db_id", "default") if context else "default"
            
            # Try to get schema information from the database service
            try:
                from services.database_service import database_service
                schema_result = asyncio.run(database_service.get_schema(db_id))
                
                if schema_result.get("status") == "success" and "data" in schema_result:
                    tables = schema_result["data"].get("tables", [])
                    
                    # Format schema information for the prompt
                    if tables:
                        schema_info = "\n\nDatabase Schema Information:\n"
                        for table in tables:
                            table_name = table.get("name", "")
                            schema_info += f"- Table: {table_name}\n"
                            
                            columns = table.get("columns", [])
                            if columns:
                                schema_info += "  Columns:\n"
                                for col in columns:
                                    col_name = col.get("name", "")
                                    col_type = col.get("type", "")
                                    schema_info += f"    - {col_name} ({col_type})\n"
            except Exception as e:
                print(f"Error getting schema: {str(e)}")
                # Continue without schema information
            
            # Build system prompt with schema information if available
            system_prompt = (
                "You are an NLU (Natural Language Understanding) parser that extracts structured information from user queries. "
                "Your task is to identify the user's intent, entities, and other relevant information. "
                "Respond ONLY with a valid JSON object that has the following structure:\n"
                "{\n"
                "  \"intent\": \"identified intent\",\n"
                "  \"confidence\": float between 0 and 1,\n"
                "  \"entities\": [\n"
                "    {\"name\": \"entity_name\", \"value\": \"entity_value\", \"type\": \"entity_type\"}\n"
                "  ],\n"
                "  \"context_needs\": [\"list of additional context needed\"],\n"
                "  \"ambiguities\": [\"list of potential ambiguities\"],\n"
                "  \"processed_query\": \"normalized query text\",\n"
                "  \"original_query\": \"original query text\",\n"
                "  \"suggested_sql\": \"optional SQL query if applicable\"\n"
                "}\n\n"
                "Valid intents: data_retrieval, report_generation, trend_analysis, comparison, aggregation, prediction, anomaly_detection, unknown\n"
                "Entity types can include: metric, filter, date, dimension, table, column, value, aggregation, function\n\n"
                "Be precise and literal in your intent classification. If you're unsure, use 'unknown' with a lower confidence score."
                f"{schema_info}\n\n"
                "If you have schema information, use actual table and column names in the suggested_sql field instead of placeholders like <table> or <columns>.\n"
                "If schema information is NOT available, you MUST STILL provide a suggested_sql template with placeholders.\n"
                "For ambiguous queries (e.g. 'show me top 5 rows'), try to resolve ambiguities by using the most appropriate table from the schema when available.\n"
                "IMPORTANT: For ANY query, ALWAYS provide a suggested_sql, even if it uses placeholders. Never return null for suggested_sql.\n"
                "For 'show me top 5 rows' without schema info, use: SELECT <columns> FROM <table> LIMIT 5"
            )
            
            # Build user prompt with query and context
            user_prompt = f"Parse this query: {query}\nContext: {context_str}"
            
            # Call the model with structured prompts
            response = self.run(
                system_prompt + "\n\nUser: " + user_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Parse the response text as JSON
            try:
                # Handle different response formats
                if hasattr(response, 'content'):
                    response_text = response.content
                elif hasattr(response, 'text'):
                    response_text = response.text
                else:
                    response_text = str(response)
                
                # Check if the response is wrapped in markdown code blocks and clean it
                if response_text.strip().startswith("```") and response_text.strip().endswith("```"):
                    # Extract the content between the code block markers
                    lines = response_text.strip().split("\n")
                    # Remove the first line (```json) and the last line (```)
                    content_lines = lines[1:-1]
                    response_text = "\n".join(content_lines)
                # Also handle case where it's ```json\n...\n``` (with json in first line)
                elif response_text.strip().startswith("```json") and response_text.strip().endswith("```"):
                    # Extract the content between the code block markers
                    lines = response_text.strip().split("\n")
                    # Remove the first line (```json) and the last line (```)
                    content_lines = lines[1:-1]
                    response_text = "\n".join(content_lines)
                
                # Now try to parse the cleaned JSON
                result = json.loads(response_text)
                # Ensure the original query is included
                if "original_query" not in result:
                    result["original_query"] = query
                return result
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Response text: {response_text}")
                
                # Try to extract JSON part if there's text around it
                if "{" in response_text and "}" in response_text:
                    try:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        json_only = response_text[json_start:json_end]
                        result = json.loads(json_only)
                        if "original_query" not in result:
                            result["original_query"] = query
                        return result
                    except json.JSONDecodeError:
                        pass
                
                # Fallback to a minimal response
                return {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "entities": [],
                    "context_needs": [],
                    "ambiguities": [],
                    "processed_query": query,
                    "original_query": query,
                    "error": str(e)
                }
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return a minimal error response
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": [],
                "context_needs": [],
                "ambiguities": [],
                "processed_query": query,
                "original_query": query,
                "error": str(e)
            }
    
    def process(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process the input text and extract intent, entities and parameters.
        
        Args:
            input_text: User's natural language query
            context: Additional context (user info, session data, etc.)
            
        Returns:
            Dictionary containing the NLU results
        """
        try:
            # Context management
            if context is None:
                context = {}
            
            # Basic pre-processing
            cleaned_input = self._preprocess_text(input_text)
            
            # Extract intent for the user's query
            intent_data = self._extract_intent(cleaned_input, context)
            
            # Get entities
            entities = self._extract_entities(cleaned_input, context)
            
            # Set up the response data
            response_data = {
                "intent": intent_data,
                "entities": entities,
                "preprocessed_text": cleaned_input,
                "original_text": input_text
            }
            
            # Determine query type
            query_type = self._determine_query_type(intent_data, entities)
            response_data["query_type"] = query_type
            
            # Return a proper dictionary directly instead of using success_response
            return {
                "status": "success",
                "message": "NLU processing complete",
                "data": response_data
            }
            
        except Exception as e:
            # Return a proper dictionary directly instead of using error_response
            return {
                "status": "error",
                "message": f"Failed to process natural language input: {str(e)}",
                "errors": [{"type": "nlu_processing_error", "message": str(e)}]
            }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess input text for better NLU processing.
        
        Args:
            text: Raw input text
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
            
        # Remove excessive whitespace and normalize
        cleaned_text = " ".join(text.split())
        
        # Remove any problematic characters if needed
        # This could be expanded based on specific requirements
        
        return cleaned_text
        
    def _extract_intent(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract intent from the user's query.
        
        Args:
            text: Preprocessed text
            context: Additional context
            
        Returns:
            Intent information with confidence
        """
        # Process the query with the internal intent detection
        intent_result = self.process_query(text, context)
        
        # Extract intent and confidence
        intent = intent_result.get("intent", "unknown")
        confidence = intent_result.get("confidence", 0.0)
        
        return {
            "name": intent,
            "confidence": confidence
        }
    
    def _extract_entities(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from the user's query.
        
        Args:
            text: Preprocessed text
            context: Additional context
            
        Returns:
            List of extracted entities
        """
        # Process the query with the internal entity extraction
        entity_result = self.process_query(text, context)
        
        # Extract entities list
        entities = entity_result.get("entities", [])
        
        # Format entities if needed
        formatted_entities = []
        for entity in entities:
            formatted_entity = {
                "name": entity.get("name", ""),
                "value": entity.get("value", ""),
                "type": entity.get("type", "unknown")
            }
            formatted_entities.append(formatted_entity)
        
        return formatted_entities
    
    def _determine_query_type(self, intent: Dict[str, Any], entities: List[Dict[str, Any]]) -> str:
        """Determine the query type based on intent and entities.
        
        Args:
            intent: Intent information
            entities: Extracted entities
            
        Returns:
            Query type classification
        """
        # Classify based on intent name
        intent_name = intent.get("name", "").lower()
        
        if "retrieval" in intent_name or "data" in intent_name:
            return "retrieval"
        elif "report" in intent_name or "visualization" in intent_name:
            return "report"
        elif "trend" in intent_name or "analysis" in intent_name:
            return "analysis"
        elif "comparison" in intent_name:
            return "comparison"
        elif "prediction" in intent_name or "forecast" in intent_name:
            return "prediction"
        else:
            # If intent not recognized, try to determine from entities
            entity_types = [e.get("type", "").lower() for e in entities]
            
            if "date_range" in entity_types or "time_period" in entity_types:
                return "trend_analysis"
            elif "comparison" in entity_types:
                return "comparison"
            elif "metric" in entity_types:
                return "aggregation"
                
            # Default to basic retrieval
            return "retrieval" 