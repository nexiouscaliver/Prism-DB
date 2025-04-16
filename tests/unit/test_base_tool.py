"""
Unit tests for the BaseTool class.
"""
import pytest
from unittest.mock import patch, AsyncMock
from agents.tools.base import BaseTool


class TestBaseTool:
    """Tests for the BaseTool class."""

    def test_base_tool_initialization(self):
        """Test that BaseTool can be initialized with properties."""
        tool = BaseTool(name="test_tool", description="A test tool")
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
    
    def test_string_representation(self):
        """Test the string representation of a BaseTool."""
        tool = BaseTool(name="test_tool")
        
        assert str(tool) == "BaseTool(name=test_tool)"
        assert repr(tool) == "BaseTool(name=test_tool)"
    
    async def test_run_method_not_implemented(self):
        """Test that the run method raises NotImplementedError."""
        tool = BaseTool()
        
        with pytest.raises(NotImplementedError):
            await tool.run(param="value")


class TestToolSubclass:
    """Tests for a subclass of BaseTool."""
    
    class TestTool(BaseTool):
        """A concrete implementation of BaseTool for testing."""
        
        name = "test_tool"
        description = "A test tool"
        
        async def run(self, **kwargs):
            """Implement the run method."""
            return {"status": "success", "param": kwargs.get("param")}
    
    def test_subclass_initialization(self):
        """Test that a BaseTool subclass can be initialized."""
        tool = self.TestTool()
        
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
    
    @pytest.mark.asyncio
    async def test_subclass_run_method(self):
        """Test that a subclass can implement the run method."""
        tool = self.TestTool()
        
        result = await tool.run(param="test_value")
        
        assert result["status"] == "success"
        assert result["param"] == "test_value" 