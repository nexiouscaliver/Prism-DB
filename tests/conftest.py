"""
Pytest configuration for PrismDB test suite.

This module contains fixtures and configuration for testing PrismDB components.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock

from app import create_app
from config.databases import DatabaseConfig


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(testing=True)
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def mock_database_tool():
    """Create a mock database tool for testing."""
    mock_tool = MagicMock()
    mock_tool.execute_query.return_value = {"status": "success", "results": []}
    mock_tool.list_tables.return_value = {"status": "success", "tables": []}
    mock_tool.get_table_schema.return_value = {"status": "success", "schema": []}
    return mock_tool


@pytest.fixture
def mock_prism_sql_tools():
    """Create a mock PrismSQLTools instance for testing."""
    mock_tool = MagicMock()
    mock_tool.run.return_value = {"status": "success", "results": []}
    return mock_tool


@pytest.fixture
def test_db_config():
    """Create a test database configuration."""
    return DatabaseConfig(
        id="test_db",
        name="Test Database",
        type="sqlite",
        connection_string="sqlite:///:memory:",
        enabled=True,
        readonly=False
    )


@pytest.fixture
def in_memory_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def in_memory_db_session(in_memory_db_engine):
    """Create a database session for the in-memory database."""
    Session = sessionmaker(bind=in_memory_db_engine)
    session = Session()
    yield session
    session.close() 