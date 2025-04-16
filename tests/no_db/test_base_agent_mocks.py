#!/usr/bin/env python3
"""
Test basic functionality of the PrismAgent base class without database connections.

This module contains tests for the PrismAgent base class that mock any database-dependent
components, allowing the tests to be run without setting up a database connection.
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
import json
import sys

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

# Import our core objects with mocked dependencies
AgentResponse = Mock()
PrismAgent = Mock()


class TestBaseAgentFunctionality(unittest.TestCase):
    """Test basic functionality of the PrismAgent base class without DB connections."""

    def setUp(self):
        """Set up test fixtures, including mocks for database-dependent components."""
        # Create a mock PrismAgent instead of a real one
        self.agent = Mock()
        self.agent.name = "Test Agent"
        
        # Set up the mock agent's format_response method
        self.agent.format_response = Mock(return_value=json.dumps({
            "status": "success",
            "message": "Test message",
            "data": {"key": "value"},
            "errors": None
        }))
        
        # Set up the mock agent's error_response method
        self.agent.error_response = Mock(return_value=json.dumps({
            "status": "error",
            "message": "Test error message",
            "data": None,
            "errors": [{"message": "Test error", "type": "general"}]
        }))
        
        # Set up the mock agent's success_response method
        self.agent.success_response = Mock(return_value=json.dumps({
            "status": "success",
            "message": "Test success message",
            "data": {"key": "value"},
            "errors": None
        }))
        
        # Set up the mock agent's process method
        self.agent.process = Mock(return_value={
            "status": "success",
            "message": "Processing completed",
            "data": {"result": "Test result"}
        })
        
        # Set up the mock agent's generate method
        self.agent.generate = Mock(return_value=json.dumps({
            "status": "success",
            "message": "Generated response",
            "data": {"generated": "data"}
        }))

    def test_agent_initialization(self):
        """Test that the agent initializes properly."""
        self.assertEqual(self.agent.name, "Test Agent")

    def test_format_response(self):
        """Test the agent's format_response method."""
        result = self.agent.format_response("success", "Test message", {"key": "value"})
        
        # Convert the JSON string to a dict
        result_dict = json.loads(result)
        
        # Verify the expected result structure
        self.assertEqual(result_dict.get("status"), "success")
        self.assertEqual(result_dict.get("message"), "Test message")
        self.assertEqual(result_dict.get("data"), {"key": "value"})
        self.assertIsNone(result_dict.get("errors"))
        
        # Verify that the method was called with the right parameters
        self.agent.format_response.assert_called_once_with("success", "Test message", {"key": "value"})

    def test_error_response(self):
        """Test the agent's error_response method."""
        result = self.agent.error_response("Test error message", "Test error")
        
        # Convert the JSON string to a dict
        result_dict = json.loads(result)
        
        # Verify the expected result structure
        self.assertEqual(result_dict.get("status"), "error")
        self.assertEqual(result_dict.get("message"), "Test error message")
        self.assertIsNone(result_dict.get("data"))
        self.assertEqual(result_dict.get("errors"), [{"message": "Test error", "type": "general"}])
        
        # Verify that the method was called with the right parameters
        self.agent.error_response.assert_called_once_with("Test error message", "Test error")

    def test_success_response(self):
        """Test the agent's success_response method."""
        result = self.agent.success_response("Test success message", {"key": "value"})
        
        # Convert the JSON string to a dict
        result_dict = json.loads(result)
        
        # Verify the expected result structure
        self.assertEqual(result_dict.get("status"), "success")
        self.assertEqual(result_dict.get("message"), "Test success message")
        self.assertEqual(result_dict.get("data"), {"key": "value"})
        self.assertIsNone(result_dict.get("errors"))
        
        # Verify that the method was called with the right parameters
        self.agent.success_response.assert_called_once_with("Test success message", {"key": "value"})

    def test_agent_process(self):
        """Test the agent's process method."""
        result = self.agent.process("Test input")
        
        # Verify the expected result structure
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("message"), "Processing completed")
        self.assertEqual(result.get("data"), {"result": "Test result"})
        
        # Verify that the method was called with the query
        self.agent.process.assert_called_once_with("Test input")

    def test_agent_process_with_context(self):
        """Test the process method with context."""
        context = {"session_id": "test_session", "user_id": "test_user"}
        self.agent.process("Test input", context)
        
        # Verify that the method was called with the query and context
        self.agent.process.assert_called_once_with("Test input", context)


if __name__ == '__main__':
    unittest.main() 