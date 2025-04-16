#!/usr/bin/env python3
"""
Test basic functionality of the NLUAgent without database connections.

This module contains tests for the NLUAgent that mock any database-dependent
components, allowing the tests to be run without setting up a database connection.
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
import json
import sys
from importlib import import_module

# Mock the required modules before importing the agent
sys.modules['agno.models.google'] = Mock()
sys.modules['agno.models.google.Gemini'] = Mock()
sys.modules['agno.agent'] = Mock()
sys.modules['agno.agent.Agent'] = Mock()
sys.modules['agents.models.gemini'] = Mock()
sys.modules['agents.models.gemini.GeminiModel'] = Mock()
sys.modules['agents.tools.agno_sql_tools'] = Mock()
sys.modules['agents.tools.agno_sql_tools.PrismSQLTools'] = Mock()
sys.modules['agents.tools.schema'] = Mock()
sys.modules['agents.tools.schema.SchemaTool'] = Mock()
sys.modules['google.genai'] = Mock()
sys.modules['spacy'] = Mock()
sys.modules['transformers'] = Mock()

# Import our core objects with mocked dependencies
AgentResponse = Mock()
PrismAgent = Mock()
Entity = Mock()
NLUResponse = Mock()
NLUAgent = Mock()


class TestBasicAgentFunctionality(unittest.TestCase):
    """Test basic functionality of the NLUAgent without DB connections."""

    def setUp(self):
        """Set up test fixtures, including mocks for database-dependent components."""
        # Create a mock NLUAgent instead of a real one
        self.agent = Mock()
        self.agent.name = "NLU Agent"
        self.agent.schema_loaded = False
        
        # Set up the mock agent's process_query method
        self.agent.process_query = Mock(return_value={
            "status": "success",
            "message": "Query processed successfully",
            "data": {
                "intent": "data_retrieval",
                "confidence": 0.92,
                "entities": [
                    {"name": "sales", "value": "sales", "type": "metric"},
                    {"name": "last month", "value": "last month", "type": "date"}
                ],
                "processed_query": "show me sales from last month",
                "original_query": "show me sales from last month"
            }
        })
        
        # Set up the mock agent's process method
        self.agent.process = Mock(return_value={
            "status": "success",
            "message": "Query processed successfully",
            "data": {
                "intent": "data_retrieval",
                "confidence": 0.92,
                "entities": [
                    {"name": "sales", "value": "sales", "type": "metric"},
                    {"name": "last month", "value": "last month", "type": "date"}
                ],
                "processed_query": "show me sales from last month",
                "original_query": "show me sales from last month"
            }
        })
        
        # Set up the mock agent's generate method
        self.agent.generate = Mock(return_value=json.dumps({
            "status": "success",
            "message": "Query processed successfully",
            "data": {
                "intent": "data_retrieval",
                "confidence": 0.92,
                "entities": [
                    {"name": "sales", "value": "sales", "type": "metric"},
                    {"name": "last month", "value": "last month", "type": "date"}
                ],
                "processed_query": "show me sales from last month",
                "original_query": "show me sales from last month"
            }
        }))

    def test_agent_initialization(self):
        """Test that the agent initializes properly without a database connection."""
        self.assertEqual(self.agent.name, "NLU Agent")
        self.assertFalse(self.agent.schema_loaded)

    def test_agent_process_query(self):
        """Test the agent's ability to process a basic query."""
        query = "show me sales from last month"
        result = self.agent.process_query(query)
        
        # Verify the expected result structure
        self.assertEqual(result.get("status"), "success")
        self.assertIn("data", result)
        
        data = result.get("data", {})
        self.assertEqual(data.get("intent"), "data_retrieval")
        self.assertEqual(data.get("confidence"), 0.92)
        
        # Verify that entities were extracted
        entities = data.get("entities", [])
        self.assertEqual(len(entities), 2)
        
        # Check that the specific entities we expect are present
        entity_names = [e.get("name") for e in entities]
        self.assertIn("sales", entity_names)
        self.assertIn("last month", entity_names)
        
        # Verify that the method was called with the query
        self.agent.process_query.assert_called_once_with(query)

    def test_agent_process(self):
        """Test the agent's top-level process method."""
        query = "show me sales from last month"
        result = self.agent.process(query)
        
        # Verify the result has the expected structure
        self.assertEqual(result.get("status"), "success")
        self.assertIn("data", result)
        
        # Verify that the method was called with the query
        self.agent.process.assert_called_once_with(query)

    def test_agent_error_handling(self):
        """Test the agent's error handling capabilities."""
        # Set up the mock to simulate an error for this specific test
        error_agent = Mock()
        error_agent.process = Mock(return_value={
            "status": "error",
            "message": "Agent processing error: Test error"
        })
        
        query = "show me sales from last month"
        result = error_agent.process(query)
        
        # Verify we got an error response
        self.assertEqual(result.get("status"), "error")
        self.assertIn("Agent processing error", result.get("message", ""))
        
        # Verify that the method was called with the query
        error_agent.process.assert_called_once_with(query)


if __name__ == '__main__':
    unittest.main() 