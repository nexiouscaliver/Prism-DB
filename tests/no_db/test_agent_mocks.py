"""
Tests for agent classes using mock data without requiring database connections.

These tests validate the core functionality of the agents by mocking external
dependencies, making them fast and reliable for CI/CD pipelines.
"""

import pytest
import unittest
from unittest.mock import MagicMock, patch

from agents.nlu_agent import NLUAgent
from agents.query_agent import QueryAgent
from agents.schema_agent import SchemaAgent
from agents.viz_agent import VisualizationAgent
from services.database_service import DatabaseService
from services.execution_service import ExecutionService

from tests.no_db.sample_data import (
    SAMPLE_SCHEMA,
    SAMPLE_QUERY_RESULTS,
    SAMPLE_NL_SQL_MAPPINGS
)


class TestNLUAgentWithMocks(unittest.TestCase):
    """Test NLU Agent functionality with mocked dependencies."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.mock_schema_agent = MagicMock()
        self.mock_schema_agent.get_database_schema.return_value = SAMPLE_SCHEMA["chinook"]
        
        self.nlu_agent = NLUAgent()
        self.nlu_agent._schema_agent = self.mock_schema_agent
        
        # Sample natural language query
        self.nl_query = "Show me the top 5 longest tracks"
        
        # Expected SQL query
        self.expected_sql = "SELECT Name, Milliseconds FROM Track ORDER BY Milliseconds DESC LIMIT 5"

    @patch('agents.nlu_agent.llm_service')
    def test_translate_to_sql(self, mock_llm_service):
        """Test NLU agent's ability to translate natural language to SQL."""
        # Configure the mock to return a predefined SQL query
        mock_llm_service.generate_sql_from_nl.return_value = {
            "sql": self.expected_sql,
            "explanation": "Query to find the longest tracks by duration"
        }
        
        # Call the method under test
        result = self.nlu_agent.translate_to_sql(self.nl_query, "chinook")
        
        # Verify the result
        self.assertEqual(result["sql"], self.expected_sql)
        self.assertIn("explanation", result)
        
        # Verify that the LLM service was called with correct parameters
        mock_llm_service.generate_sql_from_nl.assert_called_once()


class TestQueryAgentWithMocks(unittest.TestCase):
    """Test Query Agent functionality with mocked dependencies."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.mock_execution_service = MagicMock(spec=ExecutionService)
        self.mock_execution_service.execute_query.return_value = SAMPLE_QUERY_RESULTS["chinook_tracks"]
        
        self.query_agent = QueryAgent()
        self.query_agent._execution_service = self.mock_execution_service
        
        self.sql_query = "SELECT * FROM Track LIMIT 5"
        self.db_name = "chinook"

    def test_execute_query(self):
        """Test query agent's ability to execute SQL queries."""
        # Call the method under test
        result = self.query_agent.execute_query(self.sql_query, self.db_name)
        
        # Verify the result
        self.assertEqual(result, SAMPLE_QUERY_RESULTS["chinook_tracks"])
        
        # Verify that the execution service was called with correct parameters
        self.mock_execution_service.execute_query.assert_called_once_with(
            self.sql_query, self.db_name
        )

    def test_validate_query(self):
        """Test query validation functionality."""
        # Test valid SQL query
        valid_result = self.query_agent.validate_query("SELECT * FROM Track", self.db_name)
        self.assertTrue(valid_result["is_valid"])
        
        # Test invalid SQL query
        invalid_query = "SELCT * FROMM Track"  # Intentional typos
        with patch.object(self.query_agent, '_execution_service') as mock_service:
            mock_service.validate_query.return_value = {
                "is_valid": False,
                "error": "syntax error at or near 'SELCT'"
            }
            invalid_result = self.query_agent.validate_query(invalid_query, self.db_name)
            self.assertFalse(invalid_result["is_valid"])


class TestSchemaAgentWithMocks(unittest.TestCase):
    """Test Schema Agent functionality with mocked dependencies."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.mock_db_service = MagicMock(spec=DatabaseService)
        self.mock_db_service.get_database_schema.return_value = SAMPLE_SCHEMA["chinook"]
        self.mock_db_service.list_tables.return_value = list(SAMPLE_SCHEMA["chinook"].keys())
        
        self.schema_agent = SchemaAgent()
        self.schema_agent._db_service = self.mock_db_service
        
        self.db_name = "chinook"
        self.table_name = "Track"

    def test_get_database_schema(self):
        """Test retrieval of database schema."""
        # Call the method under test
        result = self.schema_agent.get_database_schema(self.db_name)
        
        # Verify the result
        self.assertEqual(result, SAMPLE_SCHEMA["chinook"])
        
        # Verify that the database service was called with correct parameters
        self.mock_db_service.get_database_schema.assert_called_once_with(self.db_name)

    def test_get_table_schema(self):
        """Test retrieval of table schema."""
        # Call the method under test
        result = self.schema_agent.get_table_schema(self.db_name, self.table_name)
        
        # Verify the result
        self.assertEqual(result, SAMPLE_SCHEMA["chinook"][self.table_name])
        
        # Verify that the database service was called with correct parameters
        self.mock_db_service.get_table_schema.assert_called_once_with(
            self.db_name, self.table_name
        )


class TestVisualizationAgentWithMocks(unittest.TestCase):
    """Test Visualization Agent functionality with mocked dependencies."""

    def setUp(self):
        """Set up test fixtures for each test."""
        self.visualization_agent = VisualizationAgent()
        
        # Sample query results
        self.query_results = SAMPLE_QUERY_RESULTS["chinook_tracks"]
        
        # Sample visualization settings
        self.viz_settings = {
            "type": "bar",
            "x_column": "Name",
            "y_column": "Milliseconds",
            "title": "Track Durations"
        }

    @patch('agents.viz_agent.llm_service')
    def test_recommend_visualization(self, mock_llm_service):
        """Test recommendation of visualization based on query results."""
        # Configure the mock to return predefined visualization recommendations
        mock_llm_service.recommend_visualization.return_value = self.viz_settings
        
        # Call the method under test
        result = self.visualization_agent.recommend_visualization(
            self.query_results, "Track durations"
        )
        
        # Verify the result
        self.assertEqual(result, self.viz_settings)
        
        # Verify that the LLM service was called with correct parameters
        mock_llm_service.recommend_visualization.assert_called_once()

    @patch('agents.viz_agent.generate_visualization')
    def test_generate_visualization(self, mock_generate_visualization):
        """Test generation of visualization based on query results and settings."""
        # Configure the mock to return a visualization object
        expected_viz = {"visualization_data": "base64-encoded-image"}
        mock_generate_visualization.return_value = expected_viz
        
        # Call the method under test
        result = self.visualization_agent.generate_visualization(
            self.query_results, self.viz_settings
        )
        
        # Verify the result
        self.assertEqual(result, expected_viz)
        
        # Verify that the visualization generator was called with correct parameters
        mock_generate_visualization.assert_called_once_with(
            self.query_results, self.viz_settings
        )


if __name__ == '__main__':
    unittest.main() 