import logging
import json
import os
import openai
import google.generativeai as genai
from typing import Dict, Any, List, Optional

from .base import BaseAgent

logger = logging.getLogger("prismdb.agent.nlu")

# Intent categories for database queries
INTENTS = {
    "QUERY_DATA": "Retrieve data from the database",
    "SUMMARIZE_DATA": "Summarize or aggregate data",
    "SCHEMA_INFO": "Information about database schema",
    "DATA_VISUALIZATION": "Visualize data from database",
    "COMPARISON": "Compare data across different dimensions",
    "TREND_ANALYSIS": "Analyze trends over time",
    "CORRELATION": "Find correlations between data points"
}

class ModelAPIError(Exception):
    """Error that occurs when there's an issue with the model API."""
    pass

class NLUAgent(BaseAgent):
    """
    Natural Language Understanding Agent that uses OpenAI and Google Gemini models
    to understand user queries and classify intents.
    """
    
    def __init__(self, name="nlu_agent", config=None):
        """
        Initialize the NLU agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent including API keys
        """
        super().__init__(name, config)
        self.openai_api_key = config.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
        self.gemini_api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        
        # Initialize OpenAI client if API key is available
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.logger.info("OpenAI client initialized")
        else:
            self.logger.warning("OpenAI API key not found")
        
        # Initialize Gemini client if API key is available
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.logger.info("Google Gemini client initialized")
        else:
            self.logger.warning("Gemini API key not found")
    
    async def process(self, message, context=None):
        """
        Process a natural language message and extract intent and entities.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: Intent and entities extracted from the message
        """
        context = context or {}
        query = message.get("query", "")
        
        self.log_thought(f"Processing query: {query}")
        
        try:
            # First try OpenAI for primary intent classification
            intent_result = await self._classify_intent_openai(query, context)
            
            # Then use Gemini for entity extraction
            entity_result = await self._extract_entities_gemini(query, context)
            
            # Combine results
            result = {
                "intent": intent_result,
                "entities": entity_result,
                "original_query": query
            }
            
            return result
        except Exception as e:
            self.logger.error(f"Error in NLU processing: {str(e)}")
            return {"error": f"NLU processing failed: {str(e)}"}
    
    async def _classify_intent_openai(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the intent of a query using OpenAI.
        
        Args:
            query (str): The user query
            context (dict): Additional context
            
        Returns:
            dict: Intent classification result
        """
        if not self.openai_api_key:
            raise ModelAPIError("OpenAI API key not available")
        
        schema_context = context.get("schema", "No schema available")
        
        try:
            system_prompt = (
                "You are an expert in database queries. Analyze the user's query and classify the intent.\n"
                f"Available intents: {json.dumps(INTENTS)}\n"
                f"Database schema: {json.dumps(schema_context)}\n\n"
                "Output as JSON with the following structure:\n"
                "{\n"
                '    "name": "INTENT_NAME",\n'
                '    "confidence": 0.95,\n'
                '    "description": "Brief description of what the user wants"\n'
                "}"
            )
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            self.log_thought(f"OpenAI intent classification: {result['name']} (confidence: {result['confidence']})")
            return result
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            # Fallback to simple intent matching
            return self._fallback_intent_classification(query)
    
    async def _extract_entities_gemini(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entities from a query using Google Gemini.
        
        Args:
            query (str): The user query
            context (dict): Additional context
            
        Returns:
            list: Extracted entities
        """
        if not self.gemini_api_key:
            raise ModelAPIError("Gemini API key not available")
        
        schema_context = context.get("schema", "No schema available")
        
        try:
            prompt = (
                "Extract database entities from the following query. Identify tables, columns, "
                "values, filters, aggregations, and time ranges. Output as JSON array.\n\n"
                f"Database schema: {json.dumps(schema_context)}\n\n"
                f"Query: {query}\n\n"
                "Output format example:\n"
                "[\n"
                '    {"type": "table", "value": "users", "confidence": 0.95},\n'
                '    {"type": "column", "value": "email", "confidence": 0.9},\n'
                '    {"type": "filter", "column": "age", "operator": ">", "value": 30, "confidence": 0.8},\n'
                '    {"type": "aggregation", "function": "count", "confidence": 0.85},\n'
                '    {"type": "time_range", "start": "2023-01-01", "end": "2023-12-31", "confidence": 0.7}\n'
                "]"
            )
            
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async(prompt)
            
            # Extract JSON part from the response
            result_text = response.text
            try:
                # Handle case where the model might include markdown code blocks or extra text
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                entities = json.loads(result_text)
                self.log_thought(f"Gemini extracted {len(entities)} entities")
                return entities
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON from Gemini response: {result_text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Gemini API error: {str(e)}")
            return []
    
    def _fallback_intent_classification(self, query: str) -> Dict[str, Any]:
        """
        Simple fallback intent classification when API calls fail.
        
        Args:
            query (str): The user query
            
        Returns:
            dict: Intent classification result
        """
        self.log_thought("Using fallback intent classification")
        
        # Simple keyword matching
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["schema", "table", "column", "structure"]):
            intent = "SCHEMA_INFO"
        elif any(kw in query_lower for kw in ["visual", "chart", "graph", "plot"]):
            intent = "DATA_VISUALIZATION"
        elif any(kw in query_lower for kw in ["trend", "over time", "period"]):
            intent = "TREND_ANALYSIS"
        elif any(kw in query_lower for kw in ["compare", "difference", "versus", "vs"]):
            intent = "COMPARISON"
        elif any(kw in query_lower for kw in ["total", "average", "sum", "count", "aggregate"]):
            intent = "SUMMARIZE_DATA"
        elif any(kw in query_lower for kw in ["correlation", "related", "relationship"]):
            intent = "CORRELATION"
        else:
            intent = "QUERY_DATA"
        
        return {
            "name": intent,
            "confidence": 0.6,
            "description": INTENTS.get(intent, "Query the database")
        } 