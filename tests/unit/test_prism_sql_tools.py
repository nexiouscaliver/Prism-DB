"""
Unit tests for the PrismSQLTools class.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from agents.tools.agno_sql_tools import PrismSQLTools
from config.databases import DatabaseConfig


class TestPrismSQLTools:
    """Tests for the PrismSQLTools class."""
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @patch('agents.tools.agno_sql_tools.SQLTools')
    def test_initialization(self, mock_sql_tools, mock_databases):
        """Test that PrismSQLTools initializes connections to enabled databases."""
        # Set up mock databases
        mock_databases.return_value = [
            DatabaseConfig(id="db1", name="DB1", connection_string="sqlite:///db1.db", enabled=True),
            DatabaseConfig(id="db2", name="DB2", connection_string="sqlite:///db2.db", enabled=False),
            DatabaseConfig(id="db3", name="DB3", connection_string="sqlite:///db3.db", enabled=True),
        ]
        
        # Create PrismSQLTools instance
        tool = PrismSQLTools()
        
        # Check that SQLTools was created for enabled databases only
        assert mock_sql_tools.call_count == 2
        assert "db1" in tool.sql_tools
        assert "db2" not in tool.sql_tools
        assert "db3" in tool.sql_tools
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    def test_get_sql_tool(self, mock_databases):
        """Test that _get_sql_tool returns the correct SQLTools instance."""
        # Create a mock instance with fake sql_tools
        tool = PrismSQLTools()
        tool.sql_tools = {
            "default": MagicMock(),
            "db1": MagicMock()
        }
        
        # Test getting existing tool
        assert tool._get_sql_tool("default") == tool.sql_tools["default"]
        assert tool._get_sql_tool("db1") == tool.sql_tools["db1"]
        
        # Test getting non-existent tool
        assert tool._get_sql_tool("non_existent") is None
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @pytest.mark.asyncio
    async def test_run_execute_query(self, mock_databases):
        """Test the run method with execute_query action."""
        # Create a mock instance with fake sql_tools
        tool = PrismSQLTools()
        mock_sql_tool = MagicMock()
        mock_sql_tool.run_query = AsyncMock(return_value={
            "columns": ["id", "name"],
            "rows": [[1, "test"]]
        })
        tool.sql_tools = {"default": mock_sql_tool}
        
        # Test run with execute_query action
        result = await tool.run(
            action="execute_query",
            db_id="default",
            query="SELECT * FROM test",
            params={"param": "value"}
        )
        
        # Check the result
        assert result["status"] == "success"
        assert "columns" in result
        assert "rows" in result
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @pytest.mark.asyncio
    async def test_run_list_tables(self, mock_databases):
        """Test the run method with list_tables action."""
        # Create a mock instance with fake sql_tools
        tool = PrismSQLTools()
        mock_sql_tool = MagicMock()
        mock_sql_tool.list_tables = AsyncMock(return_value=["table1", "table2"])
        tool.sql_tools = {"default": mock_sql_tool}
        
        # Test run with list_tables action
        result = await tool.run(
            action="list_tables",
            db_id="default"
        )
        
        # Check the result
        assert result["status"] == "success"
        assert "tables" in result
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @pytest.mark.asyncio
    async def test_run_get_table_schema(self, mock_databases):
        """Test the run method with get_table_schema action."""
        # Create a mock instance with fake sql_tools
        tool = PrismSQLTools()
        mock_sql_tool = MagicMock()
        mock_sql_tool.get_table_schema = AsyncMock(return_value=[
            {"column": "id", "type": "INTEGER"},
            {"column": "name", "type": "TEXT"}
        ])
        tool.sql_tools = {"default": mock_sql_tool}
        
        # Test run with get_table_schema action
        result = await tool.run(
            action="get_table_schema",
            db_id="default",
            table_name="test_table"
        )
        
        # Check the result
        assert result["status"] == "success"
        assert "schema" in result
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @pytest.mark.asyncio
    async def test_run_list_databases(self, mock_databases):
        """Test the run method with list_databases action."""
        # Set up mock databases
        mock_databases.return_value = [
            DatabaseConfig(id="db1", name="DB1", type="sqlite", connection_string="sqlite:///db1.db", enabled=True, readonly=False),
            DatabaseConfig(id="db2", name="DB2", type="sqlite", connection_string="sqlite:///db2.db", enabled=True, readonly=True),
        ]
        
        # Create a mock instance with fake sql_tools
        tool = PrismSQLTools()
        tool.sql_tools = {"db1": MagicMock(), "db2": MagicMock()}
        
        # Test run with list_databases action
        result = await tool.run(action="list_databases")
        
        # Check the result
        assert result["status"] == "success"
        assert "databases" in result
        assert len(result["databases"]) == 2
        assert result["databases"][0]["id"] == "db1"
        assert result["databases"][1]["id"] == "db2"
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @pytest.mark.asyncio
    async def test_run_unknown_action(self, mock_databases):
        """Test the run method with an unknown action."""
        # Create a mock instance
        tool = PrismSQLTools()
        
        # Test run with unknown action
        result = await tool.run(action="unknown_action")
        
        # Check the result
        assert result["status"] == "error"
        assert "message" in result
        assert "Unknown action" in result["message"]
        assert "valid_actions" in result
    
    @patch('agents.tools.agno_sql_tools.DATABASES')
    @pytest.mark.asyncio
    async def test_run_with_invalid_db_id(self, mock_databases):
        """Test the run method with an invalid database ID."""
        # Create a mock instance with fake sql_tools
        tool = PrismSQLTools()
        tool.sql_tools = {"default": MagicMock()}
        
        # Test run with invalid db_id
        result = await tool.run(
            action="execute_query",
            db_id="non_existent",
            query="SELECT * FROM test"
        )
        
        # Check the result
        assert result["status"] == "error"
        assert "message" in result
        assert "not found" in result["message"]
        assert "available_databases" in result 