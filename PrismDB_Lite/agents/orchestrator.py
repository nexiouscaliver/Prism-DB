import asyncio
import logging
import yaml
import json
import os
from pathlib import Path

from .base import BaseAgent

logger = logging.getLogger("prismdb.agent.orchestrator")

class AgentTeamMode:
    """Modes for agent team collaboration."""
    ROUTE = "route"
    COORDINATE = "coordinate"
    COLLABORATE = "collaborate"

class Orchestrator(BaseAgent):
    """
    Main orchestrator for coordinating the multi-agent workflow.
    Implements Team 2.0 architecture with 3 collaboration modes.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the orchestrator.
        
        Args:
            config_path (str, optional): Path to the agent teams configuration file
        """
        super().__init__("orchestrator")
        self.agents = {}
        self.team_config = {}
        self.processing_mode = AgentTeamMode.ROUTE
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path):
        """
        Load agent team configuration from a YAML file.
        
        Args:
            config_path (str): Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.team_config = config
            self.logger.info(f"Loaded team configuration from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            raise ValueError(f"Failed to load configuration: {str(e)}")
    
    def register_agent(self, agent_name, agent_instance):
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_name (str): Name of the agent
            agent_instance (BaseAgent): Instance of the agent
        """
        self.agents[agent_name] = agent_instance
        self.logger.info(f"Registered agent: {agent_name}")
    
    def set_mode(self, mode):
        """
        Set the processing mode for the agent team.
        
        Args:
            mode (str): Processing mode (route, coordinate, or collaborate)
        """
        if mode not in [AgentTeamMode.ROUTE, AgentTeamMode.COORDINATE, AgentTeamMode.COLLABORATE]:
            raise ValueError(f"Invalid mode: {mode}")
        
        self.processing_mode = mode
        self.logger.info(f"Set processing mode to: {mode}")
    
    async def process(self, message, context=None):
        """
        Process a message using the appropriate strategy based on the current mode.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: The aggregated response from agents
        """
        context = context or {}
        self.shared_context.update(context)
        
        # Process based on the current mode
        if self.processing_mode == AgentTeamMode.ROUTE:
            return await self._process_route_mode(message)
        elif self.processing_mode == AgentTeamMode.COORDINATE:
            return await self._process_coordinate_mode(message)
        elif self.processing_mode == AgentTeamMode.COLLABORATE:
            return await self._process_collaborate_mode(message)
        else:
            # Default to route mode
            return await self._process_route_mode(message)
    
    async def _process_route_mode(self, message):
        """
        Process in route mode - route the query to the most appropriate agent.
        
        Args:
            message (dict): The message to process
            
        Returns:
            dict: The response from the selected agent
        """
        self.log_thought("Processing in ROUTE mode - selecting most appropriate agent")
        
        # Start with NLU agent to classify the intent
        if "nlu_agent" in self.agents:
            nlu_result = await self.agents["nlu_agent"].process(message, self.shared_context)
            self.update_context("intent", nlu_result.get("intent"))
            self.update_context("entities", nlu_result.get("entities"))
            
            # Determine which agent to route to based on intent
            intent = nlu_result.get("intent", {}).get("name", "")
            
            if "schema" in intent.lower():
                target_agent = "schema_agent"
            elif "sql" in intent.lower() or "query" in intent.lower():
                target_agent = "sql_agent"
            elif "visual" in intent.lower() or "chart" in intent.lower():
                target_agent = "visualization_agent"
            else:
                # Default to SQL agent for database queries
                target_agent = "sql_agent"
            
            self.log_thought(f"Routing to {target_agent} based on intent: {intent}")
            
            # Process with the target agent
            if target_agent in self.agents:
                result = await self.agents[target_agent].process(message, self.shared_context)
                return result
            else:
                return {"error": f"Agent {target_agent} not found"}
        else:
            return {"error": "NLU agent not available for routing"}
    
    async def _process_coordinate_mode(self, message):
        """
        Process in coordinate mode - execute tasks in parallel where possible.
        
        Args:
            message (dict): The message to process
            
        Returns:
            dict: The combined responses from all agents
        """
        self.log_thought("Processing in COORDINATE mode - parallel execution")
        
        results = {}
        
        # First, get NLU processing and schema information in parallel
        tasks = []
        if "nlu_agent" in self.agents:
            tasks.append(self.agents["nlu_agent"].process(message, self.shared_context))
        if "schema_agent" in self.agents:
            tasks.append(self.agents["schema_agent"].process(message, self.shared_context))
        
        if tasks:
            parallel_results = await asyncio.gather(*tasks)
            
            # Update context with results
            if "nlu_agent" in self.agents:
                nlu_result = parallel_results[0]
                results["nlu"] = nlu_result
                self.update_context("intent", nlu_result.get("intent"))
                self.update_context("entities", nlu_result.get("entities"))
            
            if "schema_agent" in self.agents and "nlu_agent" in self.agents:
                schema_result = parallel_results[1]
                results["schema"] = schema_result
                self.update_context("schema", schema_result.get("schema"))
        
        # Then, generate SQL based on NLU and schema
        if "sql_agent" in self.agents:
            sql_result = await self.agents["sql_agent"].process(message, self.shared_context)
            results["sql"] = sql_result
            self.update_context("sql", sql_result.get("sql"))
        
        # Execute the SQL if available
        if "execution_agent" in self.agents and "sql" in self.shared_context:
            execution_result = await self.agents["execution_agent"].process(
                {"sql": self.shared_context.get("sql")}, 
                self.shared_context
            )
            results["execution"] = execution_result
            self.update_context("result", execution_result.get("result"))
        
        # Generate visualization if results are available
        if "visualization_agent" in self.agents and "result" in self.shared_context:
            viz_result = await self.agents["visualization_agent"].process(
                {"data": self.shared_context.get("result")},
                self.shared_context
            )
            results["visualization"] = viz_result
        
        return results
    
    async def _process_collaborate_mode(self, message):
        """
        Process in collaborate mode - agents work together to reach consensus.
        
        Args:
            message (dict): The message to process
            
        Returns:
            dict: The consensus response from all agents
        """
        self.log_thought("Processing in COLLABORATE mode - reaching consensus")
        
        # First, get NLU understanding
        if "nlu_agent" in self.agents:
            nlu_result = await self.agents["nlu_agent"].process(message, self.shared_context)
            self.update_context("intent", nlu_result.get("intent"))
            self.update_context("entities", nlu_result.get("entities"))
        
        # Get schema information
        if "schema_agent" in self.agents:
            schema_result = await self.agents["schema_agent"].process(message, self.shared_context)
            self.update_context("schema", schema_result.get("schema"))
        
        # Generate SQL through collaboration
        # We'll generate multiple SQL candidates and select the best one
        sql_candidates = []
        
        # Generate a candidate from the NLU+Schema information
        if "sql_agent" in self.agents:
            sql_result = await self.agents["sql_agent"].process(message, self.shared_context)
            sql_candidates.append({
                "sql": sql_result.get("sql"),
                "confidence": sql_result.get("confidence", 0.5),
                "source": "sql_agent"
            })
        
        # We could have other agents contribute SQL candidates here
        
        # Select the best candidate based on confidence
        if sql_candidates:
            best_candidate = max(sql_candidates, key=lambda x: x["confidence"])
            self.update_context("sql", best_candidate["sql"])
            self.log_thought(f"Selected SQL from {best_candidate['source']} with confidence {best_candidate['confidence']}")
        
        # Execute the consensus SQL
        if "execution_agent" in self.agents and "sql" in self.shared_context:
            execution_result = await self.agents["execution_agent"].process(
                {"sql": self.shared_context.get("sql")}, 
                self.shared_context
            )
            self.update_context("result", execution_result.get("result"))
            
            # Generate visualization if results are available
            if "visualization_agent" in self.agents and "result" in self.shared_context:
                viz_result = await self.agents["visualization_agent"].process(
                    {"data": self.shared_context.get("result")},
                    self.shared_context
                )
                self.update_context("visualization", viz_result.get("visualization"))
        
        # Compile the final consensus result
        return {
            "intent": self.shared_context.get("intent"),
            "sql": self.shared_context.get("sql"),
            "result": self.shared_context.get("result"),
            "visualization": self.shared_context.get("visualization")
        }
    
    def export_context(self):
        """
        Export the current shared context.
        
        Returns:
            dict: The current shared context
        """
        return self.shared_context
    
    def import_context(self, context):
        """
        Import a shared context.
        
        Args:
            context (dict): The context to import
        """
        self.shared_context = context 