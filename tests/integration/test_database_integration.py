"""
Integration tests for database connectivity.
"""
import pytest
from sqlalchemy import Table, Column, Integer, String, MetaData, select, text

from config.databases import DatabaseConfig
from agents.tools.database import DatabaseTool


class TestDatabaseIntegration:
    """Integration tests for database functionality."""
    
    @pytest.fixture
    def setup_test_db(self, in_memory_db_engine):
        """Set up a test database with a sample table."""
        metadata = MetaData()
        
        # Create a test table
        users = Table(
            'users',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String),
            Column('email', String)
        )
        
        # Create the table in the database
        metadata.create_all(in_memory_db_engine)
        
        # Insert test data
        with in_memory_db_engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO users (name, email) VALUES "
                "('User 1', 'user1@example.com'), "
                "('User 2', 'user2@example.com'), "
                "('User 3', 'user3@example.com')"
            ))
            conn.commit()
            
        return in_memory_db_engine
    
    def test_execute_query(self, setup_test_db):
        """Test executing a SQL query against a database."""
        # Initialize DatabaseTool with in-memory SQLite connection
        db_tool = DatabaseTool(connection_string="sqlite:///:memory:")
        db_tool.engine = setup_test_db  # Use the pre-configured engine
        
        # Execute a simple query
        result = db_tool.execute_query("SELECT * FROM users ORDER BY id")
        
        # Verify the results
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 3
        assert result["results"][0]["name"] == "User 1"
        assert result["results"][1]["email"] == "user2@example.com"
    
    def test_execute_query_with_params(self, setup_test_db):
        """Test executing a parameterized SQL query."""
        # Initialize DatabaseTool with in-memory SQLite connection
        db_tool = DatabaseTool(connection_string="sqlite:///:memory:")
        db_tool.engine = setup_test_db  # Use the pre-configured engine
        
        # Execute a parameterized query
        result = db_tool.execute_query(
            "SELECT * FROM users WHERE name = :name",
            {"name": "User 2"}
        )
        
        # Verify the results
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "User 2"
        assert result["results"][0]["email"] == "user2@example.com"
    
    def test_list_tables(self, setup_test_db):
        """Test listing tables in a database."""
        # Initialize DatabaseTool with in-memory SQLite connection
        db_tool = DatabaseTool(connection_string="sqlite:///:memory:")
        db_tool.engine = setup_test_db  # Use the pre-configured engine
        
        # Get the list of tables
        result = db_tool.list_tables()
        
        # Verify the results
        assert result["status"] == "success"
        assert "tables" in result
        assert "users" in [table["table_name"] for table in result["tables"]]
    
    def test_get_table_schema(self, setup_test_db):
        """Test getting schema information for a table."""
        # Initialize DatabaseTool with in-memory SQLite connection
        db_tool = DatabaseTool(connection_string="sqlite:///:memory:")
        db_tool.engine = setup_test_db  # Use the pre-configured engine
        
        # Get the schema for the users table
        result = db_tool.get_table_schema("users")
        
        # Verify the results
        assert result["status"] == "success"
        assert "schema" in result
        
        # Check that all expected columns are present
        columns = [col["column_name"] for col in result["schema"]]
        assert "id" in columns
        assert "name" in columns
        assert "email" in columns
        
        # Check column types
        id_col = next(col for col in result["schema"] if col["column_name"] == "id")
        assert "integer" in id_col["data_type"].lower()
        
        name_col = next(col for col in result["schema"] if col["column_name"] == "name")
        assert "varchar" in name_col["data_type"].lower() or "text" in name_col["data_type"].lower() 