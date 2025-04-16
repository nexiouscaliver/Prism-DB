"""
Integration tests for the PrismDB API endpoints.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
from flask_jwt_extended import create_access_token


class TestQueryEndpoints:
    """Tests for the query processing API endpoints."""
    
    @pytest.fixture
    def test_headers(self, app):
        """Create test authorization headers."""
        with app.app_context():
            # Create a test access token
            access_token = create_access_token(
                identity="test_user",
                additional_claims={"prisms": ["default::read", "default::write"]}
            )
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            return headers
    
    @patch('app.api.v1.query_routes.orchestrator.process_query')
    def test_generate_query(self, mock_process_query, client, test_headers):
        """Test the generate_query endpoint."""
        # Mock the process_query method
        mock_process_query.return_value = {
            "status": "success",
            "query": "SELECT * FROM users",
            "explanation": "This query retrieves all users"
        }
        
        # Test the endpoint
        response = client.post(
            "/api/v1/query/generate",
            data=json.dumps({"query": "Get all users", "db_id": "default"}),
            headers=test_headers
        )
        
        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["query"] == "SELECT * FROM users"
        
        # Verify the method was called with correct arguments
        mock_process_query.assert_called_once()
        args, kwargs = mock_process_query.call_args
        assert args[0] == "Get all users"
        assert kwargs.get("context", {}).get("db_id") == "default"
    
    @patch('app.api.v1.query_routes.orchestrator.process_multi_db_query')
    def test_generate_multi_db_query(self, mock_process_multi_db, client, test_headers):
        """Test the generate_multi_db_query endpoint."""
        # Mock the process_multi_db_query method
        mock_process_multi_db.return_value = {
            "status": "success",
            "results": [
                {
                    "db_id": "db1",
                    "query": "SELECT * FROM users",
                    "explanation": "This query retrieves all users from db1"
                },
                {
                    "db_id": "db2",
                    "query": "SELECT * FROM customers",
                    "explanation": "This query retrieves all customers from db2"
                }
            ]
        }
        
        # Test the endpoint
        response = client.post(
            "/api/v1/query/multi-db",
            data=json.dumps({"query": "Get all user data across all databases"}),
            headers=test_headers
        )
        
        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["results"]) == 2
        assert data["results"][0]["db_id"] == "db1"
        assert data["results"][1]["db_id"] == "db2"
        
        # Verify the method was called with correct arguments
        mock_process_multi_db.assert_called_once()
        args, kwargs = mock_process_multi_db.call_args
        assert args[0] == "Get all user data across all databases"
        assert kwargs.get("context", {}).get("multi_db") is True
    
    @patch('app.api.v1.query_routes.orchestrator.query_agent.get_available_databases')
    def test_list_databases(self, mock_get_databases, client, test_headers):
        """Test the list_databases endpoint."""
        # Mock the get_available_databases method
        mock_get_databases.return_value = [
            {"id": "db1", "name": "Database 1", "type": "postgres", "readonly": False},
            {"id": "db2", "name": "Database 2", "type": "mysql", "readonly": True}
        ]
        
        # Test the endpoint
        response = client.get(
            "/api/v1/databases",
            headers=test_headers
        )
        
        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["databases"]) == 2
        assert data["databases"][0]["id"] == "db1"
        assert data["databases"][1]["name"] == "Database 2"
    
    @patch('app.api.v1.query_routes.orchestrator.query_agent.execute_query')
    def test_execute_query(self, mock_execute_query, client, test_headers):
        """Test the execute_query endpoint."""
        # Mock the execute_query method
        mock_execute_query.return_value = {
            "status": "success",
            "columns": ["id", "name", "email"],
            "rows": [
                [1, "John Doe", "john@example.com"],
                [2, "Jane Smith", "jane@example.com"]
            ]
        }
        
        # Test the endpoint
        response = client.post(
            "/api/v1/query/execute",
            data=json.dumps({
                "sql": "SELECT * FROM users",
                "db_id": "default",
                "parameters": {}
            }),
            headers=test_headers
        )
        
        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["columns"] == ["id", "name", "email"]
        assert len(data["rows"]) == 2
        
        # Verify the method was called with correct arguments
        mock_execute_query.assert_called_once_with(
            "SELECT * FROM users", {}, db_id="default"
        )
    
    def test_missing_query(self, client, test_headers):
        """Test error handling for missing query."""
        # Test the endpoint with an empty query
        response = client.post(
            "/api/v1/query/generate",
            data=json.dumps({"query": "", "db_id": "default"}),
            headers=test_headers
        )
        
        # Check the response
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "VALIDATION_ERROR" in data["error"]["code"]
    
    @patch('app.api.v1.query_routes.check_rate_limit')
    def test_rate_limit_exceeded(self, mock_check_rate_limit, client, test_headers):
        """Test rate limit error handling."""
        # Mock the rate limit check to return rate limited
        mock_check_rate_limit.return_value = (True, 60)  # Limited, retry after 60 seconds
        
        # Test the endpoint
        response = client.post(
            "/api/v1/query/generate",
            data=json.dumps({"query": "Get all users", "db_id": "default"}),
            headers=test_headers
        )
        
        # Check the response
        assert response.status_code == 429
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "RATE_LIMIT_EXCEEDED" in data["error"]["code"]
        assert "60 seconds" in data["error"]["message"] 