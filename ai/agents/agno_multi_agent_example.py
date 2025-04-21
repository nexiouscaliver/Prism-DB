"""
Multi-Agent SQL and Visualization System using Agno Team Capabilities.

This module implements a multi-agent system for database operations:
1. Schema Agent - Analyzes database structure
2. Query Agent - Converts natural language to SQL
3. Visualization Agent - Creates charts from query results
"""
from typing import Dict, Any, List, Optional, Union, Tuple
import asyncio
import json
import logging
import re
import os
from datetime import datetime

from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.models.anthropic.claude import Claude
from agno.tools.sql import SQLTools
from agno.tools.plotly import PlotlyChartTools
from agno.team import Team

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Helper function to get API keys from environment or fallback
def get_api_key(provider: str, fallback: Optional[str] = None) -> Optional[str]:
    """Get API key for a provider with fallback."""
    if provider.lower() == "openai":
        return os.environ.get("OPENAI_API_KEY", fallback)
    elif provider.lower() == "google":
        return os.environ.get("GOOGLE_API_KEY", fallback)
    elif provider.lower() == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY", fallback)
    return fallback


class DatabaseTeam:
    """A team of agents for database operations and visualization."""
    
    def __init__(
        self,
        connection_string: str,
        model_id: str = "gemini-2.0-flash",
        team_model_id: Optional[str] = None
    ):
        """Initialize the database team.
        
        Args:
            connection_string: Database connection string
            model_id: Model ID for individual agents
            team_model_id: Optional different model for the team coordinator
        """
        self.connection_string = connection_string
        self.schema_agent = self._create_schema_agent(model_id)
        self.query_agent = self._create_query_agent(model_id)
        self.viz_agent = self._create_viz_agent(model_id)
        
        # Create the team with all agents
        self.team = Team(
            mode="coordinate",  # Use coordinate mode for sequential processing
            members=[self.schema_agent, self.query_agent, self.viz_agent],
            model=self._initialize_model(team_model_id or model_id),
            success_criteria="Generate accurate SQL queries from natural language and produce insightful visualizations.",
            instructions=[
                "First analyze the database schema",
                "Then generate appropriate SQL for the user's question", 
                "Finally create a visualization from the query results"
            ],
            show_tool_calls=True,
            markdown=True
        )
    
    def _initialize_model(self, model_id: str):
        """Initialize a model based on the model_id.
        
        Args:
            model_id: The model identifier.
            
        Returns:
            Initialized model instance.
        """
        if model_id.startswith("gpt-"):
            return OpenAIChat(
                id=model_id,
                api_key=get_api_key("openai"),
                temperature=0.2,
                top_p=0.95
            )
        elif model_id.startswith("claude-"):
            return Claude(
                id=model_id,
                api_key=get_api_key("anthropic"),
                temperature=0.2,
                top_p=0.95
            )
        else:  # Default to Gemini models
            return Gemini(
                id=model_id,
                api_key=get_api_key("google"),
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
    
    def _create_schema_agent(self, model_id: str) -> Agent:
        """Create the schema agent.
        
        Args:
            model_id: Model ID to use
            
        Returns:
            Configured schema agent
        """
        # Initialize SQLTools for schema extraction
        sql_tools = SQLTools(db_url=self.connection_string)
        
        return Agent(
            name="Schema Agent",
            role="Analyze database schema structure and relationships",
            model=self._initialize_model(model_id),
            tools=[sql_tools],
            instructions=[
                "Analyze database schema structures accurately",
                "Detect table relationships and foreign keys",
                "Identify primary keys and constraints",
                "Format responses in a clear, structured manner"
            ],
            markdown=True,
            show_tool_calls=True
        )
    
    def _create_query_agent(self, model_id: str) -> Agent:
        """Create the query agent.
        
        Args:
            model_id: Model ID to use
            
        Returns:
            Configured query agent
        """
        # Initialize SQLTools for query execution
        sql_tools = SQLTools(db_url=self.connection_string)
        
        return Agent(
            name="Query Agent",
            role="Convert natural language to SQL and execute queries",
            model=self._initialize_model(model_id),
            tools=[sql_tools],
            instructions=[
                "Convert natural language questions to SQL queries",
                "Use schema information from Schema Agent to write accurate SQL",
                "Ensure SQL is secure and optimized",
                "Execute queries and return structured results"
            ],
            markdown=True,
            show_tool_calls=True
        )
    
    def _create_viz_agent(self, model_id: str) -> Agent:
        """Create the visualization agent.
        
        Args:
            model_id: Model ID to use
            
        Returns:
            Configured visualization agent
        """
        # Initialize Plotly chart tools
        chart_tools = PlotlyChartTools()
        
        return Agent(
            name="Visualization Agent",
            role="Create data visualizations from query results",
            model=self._initialize_model(model_id),
            tools=[chart_tools],
            instructions=[
                "Analyze query results to determine appropriate chart type",
                "Handle time series data intelligently with line charts",
                "Use bar charts for categorical comparisons",
                "Apply pie charts only for proportion analysis with few categories",
                "Ensure visualizations are clean, labeled, and informative",
                "Provide data-driven insights alongside visualizations"
            ],
            markdown=True,
            show_tool_calls=True
        )
    
    async def process(self, question: str) -> Dict[str, Any]:
        """Process a question through the agent team.
        
        Args:
            question: Natural language question about data
            
        Returns:
            Dictionary with results from schema analysis, SQL query, and visualization
        """
        try:
            # Run the full team to process the question
            timer_start = datetime.now()
            response = await self.team.generate(
                f"Analyze the database, then create and visualize results for the query: {question}"
            )
            timer_end = datetime.now()
            
            # Extract key information from the response
            # (In a real implementation, you might want to parse the response more robustly)
            sql_match = re.search(r"```sql\s+(.*?)\s+```", response, re.DOTALL)
            sql = sql_match.group(1).strip() if sql_match else "No SQL generated"
            
            # Look for any chart URLs in the response
            chart_urls = []
            url_pattern = r'https?://[^\s<>"]+(?:png|jpg|jpeg|svg|html)'
            url_matches = re.findall(url_pattern, response)
            if url_matches:
                chart_urls = url_matches
            
            # Return structured result
            return {
                "status": "success",
                "original_question": question,
                "sql": sql,
                "visualization_urls": chart_urls,
                "full_response": response,
                "processing_time": (timer_end - timer_start).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing question: {str(e)}",
                "original_question": question
            }
    
    # Method for more direct, separate agent access if needed
    async def process_step_by_step(self, question: str) -> Dict[str, Any]:
        """Process a question step by step through individual agents.
        
        Args:
            question: Natural language question about data
            
        Returns:
            Dictionary with step-by-step results
        """
        try:
            # Step 1: Get schema information
            schema_prompt = f"Analyze the database schema for: {question}"
            schema_response = await self.schema_agent.generate(schema_prompt)
            
            # Step 2: Generate and execute SQL
            query_prompt = f"Using this schema information:\n{schema_response}\n\nGenerate SQL for: {question}"
            query_response = await self.query_agent.generate(query_prompt)
            
            # Extract SQL from response
            sql_match = re.search(r"```sql\s+(.*?)\s+```", query_response, re.DOTALL)
            sql = sql_match.group(1).strip() if sql_match else None
            
            # Step 3: Create visualization
            viz_prompt = f"Create a visualization for the SQL results of: {query_response}"
            viz_response = await self.viz_agent.generate(viz_prompt)
            
            # Return structured result with all steps
            return {
                "status": "success",
                "original_question": question,
                "schema_analysis": schema_response,
                "sql_generation": query_response,
                "sql": sql,
                "visualization": viz_response
            }
            
        except Exception as e:
            logger.error(f"Error in step-by-step process: {str(e)}")
            return {
                "status": "error",
                "message": f"Error in step-by-step process: {str(e)}",
                "original_question": question
            }


# Example usage
async def main():
    # Initialize the database team with a connection string
    connection_string = "sqlite:///example.db"
    db_team = DatabaseTeam(
        connection_string=connection_string,
        model_id="gemini-2.0-flash",
        team_model_id="gpt-4-turbo"  # Using a more capable model for coordination
    )
    
    # Process a question with the team
    result = await db_team.process(
        "What are the sales trends for our top 5 products over the last year?"
    )
    
    print(json.dumps(result, indent=2))
    
    # Alternatively, process step by step
    step_result = await db_team.process_step_by_step(
        "Who are our most valuable customers based on total order amount?"
    )
    
    print("\nStep by step result:")
    print(json.dumps(step_result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 