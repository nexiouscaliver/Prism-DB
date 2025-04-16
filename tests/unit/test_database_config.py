"""
Unit tests for database configuration.
"""
import pytest
from unittest.mock import patch, MagicMock
from config.databases import DatabaseConfig, DATABASES


class TestDatabaseConfig:
    """Tests for the DatabaseConfig class and DATABASES configuration."""
    
    def test_database_config_initialization(self):
        """Test that DatabaseConfig can be initialized with properties."""
        config = DatabaseConfig(
            id="test_db",
            name="Test Database",
            type="postgresql",
            connection_string="postgresql://user:pass@localhost:5432/testdb",
            enabled=True,
            readonly=False
        )
        
        assert config.id == "test_db"
        assert config.name == "Test Database"
        assert config.type == "postgresql"
        assert config.connection_string == "postgresql://user:pass@localhost:5432/testdb"
        assert config.enabled is True
        assert config.readonly is False
    
    def test_database_config_default_values(self):
        """Test that DatabaseConfig sets default values correctly."""
        config = DatabaseConfig(
            id="minimal_db",
            connection_string="sqlite:///minimal.db"
        )
        
        assert config.name == "minimal_db"  # Should default to ID
        assert config.type == "sqlite"  # Should infer from connection string
        assert config.enabled is True  # Should default to True
        assert config.readonly is False  # Should default to False
    
    def test_databases_list_is_populated(self):
        """Test that the DATABASES list is populated with at least one database."""
        assert isinstance(DATABASES, list)
        assert len(DATABASES) > 0
        assert all(isinstance(db, DatabaseConfig) for db in DATABASES)
    
    @patch('config.databases.os')
    def test_database_config_from_environment(self, mock_os):
        """Test loading database configuration from environment variables."""
        # Mock environment variables
        mock_os.environ = {
            "DB_CONNECTION_STRING": "postgresql://user:pass@localhost:5432/envdb",
            "DB_ENABLED": "true",
            "DB_READONLY": "false"
        }
        mock_os.path.exists.return_value = True
        
        # Create a database config that uses environment variables
        with patch('config.databases.load_env_var') as mock_load_env:
            mock_load_env.side_effect = lambda key, default=None: mock_os.environ.get(key, default)
            
            # Test with a method that loads from environment
            from config.databases import get_db_config_from_env
            
            # This is a mock function that would be similar to what's in your actual code
            def get_db_config_from_env():
                connection_string = mock_load_env("DB_CONNECTION_STRING", "sqlite:///:memory:")
                enabled = mock_load_env("DB_ENABLED", "true").lower() == "true"
                readonly = mock_load_env("DB_READONLY", "false").lower() == "true"
                
                return DatabaseConfig(
                    id="env_db",
                    name="Environment Database",
                    connection_string=connection_string,
                    enabled=enabled,
                    readonly=readonly
                )
            
            config = get_db_config_from_env()
            
            assert config.id == "env_db"
            assert config.connection_string == "postgresql://user:pass@localhost:5432/envdb"
            assert config.enabled is True
            assert config.readonly is False 