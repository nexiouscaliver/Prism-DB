"""
NLU Agent for PrismDB.

This agent is responsible for natural language understanding,
including intent classification and entity extraction.
"""
from typing import Dict, Any, List, Optional, Union, Tuple
import json
import re
import os

from agno.models.google import Gemini
from pydantic import BaseModel, Field, validator

from agents.base import PrismAgent
from agents.tools.schema import SchemaTool
from app.config import GOOGLE_API_KEY


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
        spacy_model: str = "en_core_web_sm",
        transformer_model: str = "distilbert-base-uncased-finetuned-sst-2-english",
        connection_string: Optional[str] = None,
        model_id: str = "gemini-2.0-flash",
    ):
        """Initialize the NLU Agent.
        
        Args:
            spacy_model: SpaCy model to use for NER (not used - kept for compatibility).
            transformer_model: Hugging Face model to use for intent classification (not used - kept for compatibility).
            connection_string: Database connection string.
            model_id: Gemini model identifier to use.
        """
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
        
        # Initialize schema tool with connection string
        schema_tool = SchemaTool(connection_string=connection_string)
        
        # Initialize the NLU agent with the Agno Agent base class
        super().__init__(
            name="NLU Agent",
            tools=[schema_tool],
            system_prompt=system_prompt,
            instructions=nlu_instructions,
            model_id=model_id
        )
        
        # Note: We'll use Gemini for NLP processing and intent classification instead of SpaCy/Hugging Face
        # Just print a message to inform users but don't try to load those libraries
        print("Using Gemini model for NLP processing and intent classification")

        self.model_id = model_id
            
        # Load database schema if connection string is provided
        self.schema_loaded = False
        if connection_string:
            self._load_schema()
    
    def _load_schema(self) -> None:
        """Load database schema information."""
        try:
            # Use the schema tool to get database schema
            result = self.schema_tool.list_tables()
            
            if result["status"] == "success":
                tables = result["tables"]
                
                # Add schema information to agent memory
                schema_info = f"Database contains {len(tables)} tables: "
                schema_info += ", ".join([table["name"] for table in tables])
                print(f"SCHEMA INFO: {schema_info}")
                
                # For each table, get detailed schema information
                for table in tables:
                    table_name = table["name"]
                    table_schema = self.schema_tool.get_table_schema(table_name)
                    
                    if table_schema["status"] == "success":
                        # Format column information
                        columns_info = []
                        for col in table_schema["columns"]:
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
    
    def _extract_entities_spacy(self, query: str) -> List[Dict[str, Any]]:
        """Extract entities using SpaCy.
        
        Args:
            query: Natural language query.
            
        Returns:
            List of extracted entities.
        """
        if self.nlp is None:
            return []
            
        doc = self.nlp(query)
        entities = []
        
        for ent in doc.ents:
            entity_type = self._map_spacy_entity_type(ent.label_)
            entities.append({
                "name": ent.text,
                "value": ent.text,
                "type": entity_type
            })
            
        # Also extract numeric values and dates that might not be caught as entities
        for token in doc:
            if token.like_num and not any(e["name"] == token.text for e in entities):
                entities.append({
                    "name": token.text,
                    "value": float(token.text) if token.text.replace('.', '', 1).isdigit() else token.text,
                    "type": "numeric"
                })
                
        return entities
    
    def _map_spacy_entity_type(self, spacy_type: str) -> str:
        """Map SpaCy entity types to our entity types.
        
        Args:
            spacy_type: SpaCy entity type.
            
        Returns:
            Mapped entity type.
        """
        mapping = {
            "DATE": "date",
            "TIME": "date",
            "MONEY": "metric",
            "PERCENT": "metric",
            "QUANTITY": "metric",
            "PERSON": "entity",
            "ORG": "entity",
            "GPE": "location",
            "LOC": "location",
            "PRODUCT": "entity",
            "EVENT": "entity",
            "WORK_OF_ART": "entity",
            "LAW": "entity",
            "LANGUAGE": "entity",
            "FAC": "location",
            "NORP": "entity",
        }
        
        return mapping.get(spacy_type, "unknown")
    
    def _classify_intent_transformers(self, query: str) -> Tuple[str, float]:
        """Classify intent using transformers model.
        
        Args:
            query: Natural language query.
            
        Returns:
            Tuple of (intent, confidence).
        """
        if self.tokenizer is None or self.intent_model is None:
            return "unknown", 0.0
            
        import torch
        
        # Define intent classes
        intent_classes = [
            "data_retrieval", 
            "report_generation", 
            "trend_analysis",
            "comparison",
            "aggregation",
            "prediction",
            "anomaly_detection"
        ]
        
        # Basic classification using keywords if transformer model is not available
        # This is a fallback mechanism and not meant to be sophisticated
        keywords = {
            "data_retrieval": ["show", "get", "find", "list", "display", "what is", "what are"],
            "report_generation": ["report", "generate", "create", "prepare", "build"],
            "trend_analysis": ["trend", "over time", "increase", "decrease", "growth", "pattern"],
            "comparison": ["compare", "versus", "vs", "difference", "similarities", "against"],
            "aggregation": ["average", "sum", "total", "count", "min", "max", "mean", "aggregate"],
            "prediction": ["predict", "forecast", "estimate", "project", "future", "next", "will"],
            "anomaly_detection": ["anomaly", "outlier", "unusual", "abnormal", "deviation"]
        }
        
        # Tokenize input
        inputs = self.tokenizer(query, return_tensors="pt", truncation=True, padding=True)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.intent_model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # Get the predicted class
        predicted_class = torch.argmax(predictions, dim=-1).item()
        confidence = predictions[0, predicted_class].item()
        
        if predicted_class < len(intent_classes):
            return intent_classes[predicted_class], confidence
        else:
            # Fallback to keyword matching
            for intent, intent_keywords in keywords.items():
                if any(keyword in query.lower() for keyword in intent_keywords):
                    return intent, 0.7  # Arbitrary confidence for keyword matching
                    
            return "unknown", 0.0
    
    def _classify_intent_fallback(self, query: str) -> Tuple[str, float]:
        """Classify intent using keyword matching as fallback.
        
        Args:
            query: Natural language query.
            
        Returns:
            Tuple of (intent, confidence).
        """
        # Basic classification using keywords
        # This is a fallback mechanism and not meant to be sophisticated
        keywords = {
            "data_retrieval": ["show", "get", "find", "list", "display", "what is", "what are"],
            "report_generation": ["report", "generate", "create", "prepare", "build"],
            "trend_analysis": ["trend", "over time", "increase", "decrease", "growth", "pattern"],
            "comparison": ["compare", "versus", "vs", "difference", "similarities", "against"],
            "aggregation": ["average", "sum", "total", "count", "min", "max", "mean", "aggregate"],
            "prediction": ["predict", "forecast", "estimate", "project", "future", "next", "will"],
            "anomaly_detection": ["anomaly", "outlier", "unusual", "abnormal", "deviation"]
        }
        
        query_lower = query.lower()
        
        for intent, intent_keywords in keywords.items():
            if any(keyword in query_lower for keyword in intent_keywords):
                return intent, 0.7  # Arbitrary confidence for keyword matching
                
        return "unknown", 0.0
    
    def _detect_ambiguities(self, query: str, entities: List[Dict[str, Any]]) -> List[str]:
        """Detect potential ambiguities in the query.
        
        Args:
            query: Natural language query.
            entities: Extracted entities.
            
        Returns:
            List of potential ambiguities.
        """
        ambiguities = []
        
        # Check for vague time references
        vague_time_patterns = [
            r"\b(recent|recently|latest|current|currently|now)\b",
            r"\b(this|last|previous|next)\s+(week|month|year|quarter|day)\b",
            r"\b(few|several|couple)\s+(days|weeks|months|years)\b"
        ]
        
        for pattern in vague_time_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                ambiguities.append("Time reference is ambiguous and needs clarification")
                break
                
        # Check for comparative terms without a clear reference
        comparative_patterns = [
            r"\b(more|less|higher|lower|better|worse|increase|decrease)\b",
            r"\b(than|compared to|versus|vs\.)\b"
        ]
        
        has_comparative = False
        has_comparison_target = False
        
        for pattern in comparative_patterns[:1]:  # First group: comparative terms
            if re.search(pattern, query, re.IGNORECASE):
                has_comparative = True
                break
                
        for pattern in comparative_patterns[1:]:  # Second group: comparison targets
            if re.search(pattern, query, re.IGNORECASE):
                has_comparison_target = True
                break
                
        if has_comparative and not has_comparison_target:
            ambiguities.append("Comparative reference lacks a clear baseline for comparison")
            
        # Check for ambiguous quantity references
        quantity_patterns = [
            r"\b(many|much|several|few|lot|some|most|majority)\b",
            r"\b(high|low|large|small|significant|considerable)\b"
        ]
        
        for pattern in quantity_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                ambiguities.append("Quantity reference is ambiguous and needs clarification")
                break
                
        # Check for potentially ambiguous entities
        if len(entities) > 0:
            entity_names = [e["name"].lower() for e in entities]
            entity_types = [e["type"] for e in entities]
            
            # If we have entities but no recognized metrics
            if "metric" not in entity_types and "data_retrieval" in query.lower():
                ambiguities.append("Query does not specify what metrics or data to retrieve")
                
            # Check for potential entity duplication (same entity type multiple times)
            entity_type_counts = {}
            for entity_type in entity_types:
                entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1
                
            for entity_type, count in entity_type_counts.items():
                if count > 1 and entity_type not in ["numeric", "unknown"]:
                    ambiguities.append(f"Query contains multiple {entity_type} entities, which might be ambiguous")
        
        return ambiguities
    
    def _determine_context_needs(self, query: str, intent: str, entities: List[Dict[str, Any]]) -> List[str]:
        """Determine what additional context is needed to process the query.
        
        Args:
            query: Natural language query.
            intent: Classified intent.
            entities: Extracted entities.
            
        Returns:
            List of additional context needs.
        """
        context_needs = []
        
        # Check if we need schema information
        if not self.schema_loaded:
            context_needs.append("schema_version")
            
        # Check if we need user history for context
        user_history_keywords = [
            "again", "previous", "like before", "like last time", 
            "same as", "usual", "typically", "normally"
        ]
        
        if any(keyword in query.lower() for keyword in user_history_keywords):
            context_needs.append("user_history")
            
        # Check if query needs user preferences
        preference_keywords = [
            "prefer", "preference", "favorite", "usual", "typically",
            "normally", "my", "recommend", "suggestion"
        ]
        
        if any(keyword in query.lower() for keyword in preference_keywords):
            context_needs.append("user_preferences")
            
        # Check if query needs time context
        time_context_indicators = [
            "now", "today", "current", "currently", "this",
            "period", "fiscal", "quarter", "ytd", "year to date"
        ]
        
        has_explicit_time = False
        for entity in entities:
            if entity["type"] == "date":
                has_explicit_time = True
                break
                
        if (any(indicator in query.lower() for indicator in time_context_indicators) and not has_explicit_time):
            context_needs.append("time_context")
            
        # Check if we need business rules for complex intents
        if intent in ["report_generation", "prediction", "anomaly_detection"]:
            context_needs.append("business_rules")
            
        # For trend analysis, check if we need seasonality information
        if intent == "trend_analysis":
            context_needs.append("seasonality_info")
            
        return context_needs
            
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a natural language query.
        
        Args:
            query: Natural language query.
            context: Additional context for query processing.
            
        Returns:
            Structured NLU response.
        """
        # Log query processing start
        print(f"Processing query: {query}")
        if context:
            print(f"With context: {json.dumps(context, indent=2)}")
        
        # Normalize query by trimming whitespace and converting to lowercase
        processed_query = query.strip()
        original_query = query
        
        # Use the Gemini model to process the query
        try:
            # Use Google's direct generative AI library instead of the Agno wrapper
            # This approach is more reliable for our specific use case
            import google.generativeai as genai
            
            # Configure the API
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Create the model
            model = genai.GenerativeModel(
                model_name=self.model_id,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            # Update prompt to explicitly request JSON format
            structured_prompt = f"""
            Process this database query: "{query}"
            
            Classify the intent and extract all entities. Identify any ambiguities and determine additional context needed.
            
            Allowed intents: data_retrieval, report_generation, trend_analysis, comparison, aggregation, prediction, anomaly_detection, unknown
            
            IMPORTANT: Your response MUST be valid JSON. Do not include any explanations, markdown formatting, or text outside the JSON structure.
            
            Return your analysis in the following JSON format and nothing else:
            {{
                "intent": "one of the allowed intents",
                "confidence": 0.0 to 1.0,
                "entities": [
                    {{"name": "entity name", "value": "entity value", "type": "entity type"}}
                ],
                "context_needs": ["list of additional context needed"],
                "ambiguities": ["list of ambiguities"],
                "processed_query": "normalized query",
                "original_query": "{original_query}",
                "suggested_sql": "SQL query if applicable"
            }}
            """
            
            # Generate the response with JSON formatting
            response = model.generate_content(
                structured_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Debug the response
            print(f"Response type: {type(response)}")
            print(f"Response attributes: {dir(response) if hasattr(response, '__dir__') else 'No dir method'}")
            
            # Get the text from the response
            response_text = response.text
            print(f"Response text: {response_text}")
            
            # Parse the JSON response
            try:
                # First clean the response text if it contains markdown code blocks
                if "```json" in response_text:
                    # Extract content between ```json and ```
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                        print(f"Extracted JSON from markdown: {response_text}")
                
                # Parse the JSON response
                result = json.loads(response_text)
                
                # Validate the response using the Pydantic model
                validated_response = NLUResponse(
                    intent=result.get("intent", "unknown"),
                    confidence=result.get("confidence", 0.7),
                    entities=[Entity(**entity) for entity in result.get("entities", [])],
                    context_needs=result.get("context_needs", []),
                    ambiguities=result.get("ambiguities", []),
                    processed_query=result.get("processed_query", processed_query),
                    original_query=original_query,
                    suggested_sql=result.get("suggested_sql")
                )
                
                return validated_response.dict()
                
            except json.JSONDecodeError as e:
                # If the content is not valid JSON, log the actual content for debugging
                print(f"Error parsing JSON from Gemini response: {str(e)}")
                print(f"Raw response content: {response_text}")
                return self._create_fallback_response(processed_query, original_query)
            
        except Exception as e:
            print(f"Error processing query with Gemini: {str(e)}")
            return self._create_fallback_response(processed_query, original_query)
    
    def _create_fallback_response(self, processed_query: str, original_query: str) -> Dict[str, Any]:
        """Create a fallback response when the Gemini model fails.
        
        Args:
            processed_query: The processed query text.
            original_query: The original query text.
            
        Returns:
            A fallback NLU response.
        """
        # Fallback to a simpler response if the Gemini model fails
        return {
            "intent": "unknown",
            "confidence": 0.5,
            "entities": [],
            "context_needs": ["database schema"],
            "ambiguities": ["Could not determine intent reliably"],
            "processed_query": processed_query,
            "original_query": original_query,
            "suggested_sql": None
        }
            
    def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a query with the NLU agent and return structured information.
        
        This method overrides the base PrismAgent process method to use
        specialized NLU processing when possible, falling back to the
        LLM-based processing when needed.
        
        Args:
            input_text: Natural language query to process.
            context: Optional context information.
            
        Returns:
            Structured NLU response.
        """
        # Try using our NLU pipeline first
        try:
            # Process with our NLU pipeline
            result = self.process_query(input_text, context)
            
            # If confidence is high, return the result
            if result.get("confidence", 0) >= 0.7 and result.get("intent") != "unknown":
                # Add any other enrichments needed
                return result
                
            # Otherwise, fall back to LLM processing but provide our initial analysis
            llm_context = context or {}
            llm_context["initial_nlu_analysis"] = result
            
            # Override context with our enriched one
            return super().process(input_text, llm_context)
            
        except Exception as e:
            # If our pipeline fails, fall back to the base LLM processing
            return super().process(input_text, context) 