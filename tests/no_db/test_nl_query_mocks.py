"""
Tests for natural language query processing without requiring a database connection.

This module tests the natural language query processing pipeline using mocks 
instead of actual database connections, making the tests faster and more portable.
"""

import unittest
from unittest.mock import MagicMock, patch

from tests.no_db.sample_data import (
    SAMPLE_DB_SCHEMA,
    SAMPLE_NL_QUERIES, 
    SAMPLE_SQL_OUTPUTS,
    SAMPLE_QUERY_RESULTS,
    SAMPLE_VIZ_RECOMMENDATIONS
)


class TestNLQueryProcessorWithMocks(unittest.TestCase):
    """Test the natural language query processor with mocked dependencies."""
    
    def setUp(self):
        """Set up the test environment with mocks."""
        # Create mocks for all the components
        self.mock_sql_generator = MagicMock()
        self.mock_sql_executor = MagicMock()
        self.mock_viz_recommender = MagicMock()
        
        # Create a patch for the database connection
        self.db_conn_patcher = patch('prismdb.core.nl_query_processor.get_db_connection')
        self.mock_db_conn = self.db_conn_patcher.start()
        
        # Import here to apply the patches
        from prismdb.core.nl_query_processor import NLQueryProcessor
        
        # Create the NLQueryProcessor with mocked dependencies
        self.nl_processor = NLQueryProcessor()
        
        # Replace real components with mocks
        self.nl_processor.sql_generator = self.mock_sql_generator
        self.nl_processor.sql_executor = self.mock_sql_executor
        self.nl_processor.viz_recommender = self.mock_viz_recommender
        
        # Setup default returns
        self.mock_sql_generator.generate_sql.return_value = SAMPLE_SQL_OUTPUTS[0]["sql_text"]
        self.mock_sql_executor.execute_query.return_value = SAMPLE_QUERY_RESULTS[0]["result_data"]
        self.mock_viz_recommender.recommend_visualization.return_value = SAMPLE_VIZ_RECOMMENDATIONS[0]
        
    def tearDown(self):
        """Clean up resources after tests."""
        self.db_conn_patcher.stop()
    
    def test_process_nl_query(self):
        """Test the full process of handling a natural language query."""
        nl_query = SAMPLE_NL_QUERIES[0]["query_text"]
        
        # Process the query
        result = self.nl_processor.process_query(nl_query)
        
        # Verify the SQL generator was called with the correct query
        self.mock_sql_generator.generate_sql.assert_called_once_with(nl_query)
        
        # Verify the SQL executor was called with the correct SQL
        self.mock_sql_executor.execute_query.assert_called_once_with(SAMPLE_SQL_OUTPUTS[0]["sql_text"])
        
        # Verify the visualization recommender was called with the correct data
        self.mock_viz_recommender.recommend_visualization.assert_called_once()
        
        # Verify the result contains all the expected components
        self.assertIn('sql', result)
        self.assertIn('data', result)
        self.assertIn('visualization', result)
        self.assertEqual(result['sql'], SAMPLE_SQL_OUTPUTS[0]["sql_text"])
        self.assertEqual(result['data'], SAMPLE_QUERY_RESULTS[0]["result_data"])
        self.assertEqual(result['visualization'], SAMPLE_VIZ_RECOMMENDATIONS[0])
    
    def test_error_handling_sql_generation(self):
        """Test error handling when SQL generation fails."""
        # Setup the SQL generator to raise an exception
        self.mock_sql_generator.generate_sql.side_effect = Exception("Failed to generate SQL")
        
        nl_query = SAMPLE_NL_QUERIES[0]["query_text"]
        
        # Process the query, which should handle the exception
        result = self.nl_processor.process_query(nl_query)
        
        # Verify the result contains an error message
        self.assertIn('error', result)
        self.assertIn('Failed to generate SQL', result['error'])
        
        # Verify the SQL executor and viz recommender were not called
        self.mock_sql_executor.execute_query.assert_not_called()
        self.mock_viz_recommender.recommend_visualization.assert_not_called()
    
    def test_error_handling_sql_execution(self):
        """Test error handling when SQL execution fails."""
        # Setup the SQL executor to raise an exception
        self.mock_sql_executor.execute_query.side_effect = Exception("Database error")
        
        nl_query = SAMPLE_NL_QUERIES[0]["query_text"]
        
        # Process the query, which should handle the exception
        result = self.nl_processor.process_query(nl_query)
        
        # Verify the result contains an error message
        self.assertIn('error', result)
        self.assertIn('Database error', result['error'])
        
        # Verify the SQL generator was called but the viz recommender was not
        self.mock_sql_generator.generate_sql.assert_called_once()
        self.mock_viz_recommender.recommend_visualization.assert_not_called()


class TestSQLGeneratorWithMocks(unittest.TestCase):
    """Test the SQL generator component with mocks."""
    
    def setUp(self):
        """Set up the test environment with mocks."""
        # Create a mock for the schema retriever
        self.mock_schema_retriever = MagicMock()
        self.mock_schema_retriever.get_db_schema.return_value = SAMPLE_DB_SCHEMA
        
        # Import here to apply patches if needed
        from prismdb.core.sql_generator import SQLGenerator
        
        # Create the SQLGenerator with mocked dependencies
        self.sql_generator = SQLGenerator()
        
        # Replace real components with mocks
        self.sql_generator.schema_retriever = self.mock_schema_retriever
    
    def test_generate_sql_for_customers(self):
        """Test generating SQL for a customer-related query."""
        nl_query = SAMPLE_NL_QUERIES[0]["query_text"]
        expected_sql = SAMPLE_SQL_OUTPUTS[0]["sql_text"]
        
        # Mock the method that converts NL to SQL
        self.sql_generator._convert_nl_to_sql = MagicMock(return_value=expected_sql)
        
        # Generate SQL
        sql = self.sql_generator.generate_sql(nl_query)
        
        # Verify schema retriever was called
        self.mock_schema_retriever.get_db_schema.assert_called_once()
        
        # Verify the SQL matches the expected output
        self.assertEqual(sql, expected_sql)
    
    def test_generate_sql_for_sales_analysis(self):
        """Test generating SQL for a sales analysis query."""
        nl_query = SAMPLE_NL_QUERIES[1]["query_text"]
        expected_sql = SAMPLE_SQL_OUTPUTS[1]["sql_text"]
        
        # Mock the method that converts NL to SQL
        self.sql_generator._convert_nl_to_sql = MagicMock(return_value=expected_sql)
        
        # Generate SQL
        sql = self.sql_generator.generate_sql(nl_query)
        
        # Verify the SQL matches the expected output
        self.assertEqual(sql, expected_sql)


class TestSQLExecutorWithMocks(unittest.TestCase):
    """Test the SQL executor component with mocks."""
    
    def setUp(self):
        """Set up the test environment with mocks."""
        # Create a mock for the database connection
        self.mock_db_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db_conn.cursor.return_value = self.mock_cursor
        
        # Import here to apply patches if needed
        from prismdb.core.sql_executor import SQLExecutor
        
        # Create the SQLExecutor with mocked connection
        self.sql_executor = SQLExecutor(self.mock_db_conn)
    
    def test_execute_customer_query(self):
        """Test executing a customer query."""
        sql = SAMPLE_SQL_OUTPUTS[0]["sql_text"]
        expected_result = SAMPLE_QUERY_RESULTS[0]["result_data"]
        
        # Setup the mock cursor
        self.mock_cursor.fetchall.return_value = expected_result
        self.mock_cursor.description = [
            ("customer_id", None, None, None, None, None, None),
            ("first_name", None, None, None, None, None, None),
            ("last_name", None, None, None, None, None, None),
            ("email", None, None, None, None, None, None)
        ]
        
        # Execute the query
        result = self.sql_executor.execute_query(sql)
        
        # Verify the cursor was used correctly
        self.mock_cursor.execute.assert_called_once_with(sql)
        self.mock_cursor.fetchall.assert_called_once()
        
        # Verify the result matches the expected output
        self.assertEqual(result, expected_result)
    
    def test_handling_execution_errors(self):
        """Test handling of execution errors."""
        sql = "INVALID SQL SYNTAX"
        
        # Setup the mock cursor to raise an exception
        self.mock_cursor.execute.side_effect = Exception("SQL syntax error")
        
        # Execute the query and expect an exception
        with self.assertRaises(Exception):
            self.sql_executor.execute_query(sql)


class TestVisualizationRecommenderWithMocks(unittest.TestCase):
    """Test the visualization recommender with mocks."""
    
    def setUp(self):
        """Set up the test environment."""
        # Import here to apply patches if needed
        from prismdb.core.visualization_recommender import VisualizationRecommender
        
        # Create the VisualizationRecommender
        self.viz_recommender = VisualizationRecommender()
    
    def test_recommend_for_customer_data(self):
        """Test recommending visualization for customer data."""
        sql = SAMPLE_SQL_OUTPUTS[0]["sql_text"]
        data = SAMPLE_QUERY_RESULTS[0]["result_data"]
        expected_viz = SAMPLE_VIZ_RECOMMENDATIONS[0]
        
        # Mock the method that determines the best visualization
        self.viz_recommender._determine_best_visualization = MagicMock(return_value=expected_viz)
        
        # Get recommendation
        viz = self.viz_recommender.recommend_visualization(sql, data)
        
        # Verify the visualization matches the expected output
        self.assertEqual(viz, expected_viz)
    
    def test_recommend_for_sales_data(self):
        """Test recommending visualization for sales data."""
        sql = SAMPLE_SQL_OUTPUTS[1]["sql_text"]
        data = SAMPLE_QUERY_RESULTS[1]["result_data"]
        expected_viz = SAMPLE_VIZ_RECOMMENDATIONS[1]
        
        # Mock the method that determines the best visualization
        self.viz_recommender._determine_best_visualization = MagicMock(return_value=expected_viz)
        
        # Get recommendation
        viz = self.viz_recommender.recommend_visualization(sql, data)
        
        # Verify the visualization matches the expected output
        self.assertEqual(viz, expected_viz)


if __name__ == '__main__':
    unittest.main() 