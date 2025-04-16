"""
Tests for database configuration functionality without requiring a database connection.

These tests validate that the database configuration management works correctly
by using mocked objects and sample data instead of actual database connections.
"""

import unittest
from unittest.mock import patch, MagicMock

from prismdb.config.db_config import DBConfig, DBConfigManager
from tests.no_db.sample_data import SAMPLE_DB_CONFIGS


class TestDBConfigWithMocks(unittest.TestCase):
    """Test the DBConfig class without requiring a database connection."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_config_dict = SAMPLE_DB_CONFIGS[0]
        self.db_config = DBConfig.from_dict(self.sample_config_dict)

    def test_db_config_properties(self):
        """Test that DBConfig properties return the expected values."""
        self.assertEqual(self.db_config.id, "db1")
        self.assertEqual(self.db_config.name, "Test PostgreSQL Database")
        self.assertEqual(self.db_config.db_type, "postgresql")
        self.assertEqual(
            self.db_config.connection_string,
            "postgresql://user:password@localhost:5432/testdb"
        )
        self.assertTrue(self.db_config.is_enabled)
        self.assertFalse(self.db_config.is_read_only)

    def test_to_dict(self):
        """Test that to_dict returns the correct dictionary representation."""
        config_dict = self.db_config.to_dict()
        self.assertEqual(config_dict, self.sample_config_dict)

    def test_from_dict(self):
        """Test that from_dict correctly creates a DBConfig instance."""
        config = DBConfig.from_dict(self.sample_config_dict)
        self.assertIsInstance(config, DBConfig)
        self.assertEqual(config.id, self.sample_config_dict["id"])
        self.assertEqual(config.name, self.sample_config_dict["name"])
        self.assertEqual(config.db_type, self.sample_config_dict["db_type"])
        self.assertEqual(
            config.connection_string, 
            self.sample_config_dict["connection_string"]
        )
        self.assertEqual(config.is_enabled, self.sample_config_dict["is_enabled"])
        self.assertEqual(config.is_read_only, self.sample_config_dict["is_read_only"])


class TestDBConfigManagerWithMocks(unittest.TestCase):
    """Test the DBConfigManager class without requiring a database connection."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a patched version of the DBConfigManager
        self.patcher = patch('prismdb.config.db_config.DBConfigManager._load_configs')
        self.mock_load_configs = self.patcher.start()
        
        # Configure the mock to return our sample data
        sample_configs = [DBConfig.from_dict(config) for config in SAMPLE_DB_CONFIGS]
        self.mock_load_configs.return_value = sample_configs
        
        # Create the manager with the mocked _load_configs method
        self.config_manager = DBConfigManager()
        
        # Reset the save method to avoid actually writing to disk
        self.config_manager._save_configs = MagicMock()

    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()

    def test_get_all_configs(self):
        """Test that get_all_configs returns all configurations."""
        configs = self.config_manager.get_all_configs()
        self.assertEqual(len(configs), len(SAMPLE_DB_CONFIGS))
        
        # Check that the returned configs match our sample data
        for i, config in enumerate(configs):
            self.assertEqual(config.id, SAMPLE_DB_CONFIGS[i]["id"])
            self.assertEqual(config.name, SAMPLE_DB_CONFIGS[i]["name"])

    def test_get_config_by_id(self):
        """Test that get_config_by_id returns the correct configuration."""
        config = self.config_manager.get_config_by_id("db1")
        self.assertIsNotNone(config)
        self.assertEqual(config.id, "db1")
        self.assertEqual(config.name, "Test PostgreSQL Database")
        
        # Test with non-existent ID
        config = self.config_manager.get_config_by_id("non_existent")
        self.assertIsNone(config)

    def test_get_config_by_name(self):
        """Test that get_config_by_name returns the correct configuration."""
        config = self.config_manager.get_config_by_name("Test PostgreSQL Database")
        self.assertIsNotNone(config)
        self.assertEqual(config.id, "db1")
        self.assertEqual(config.name, "Test PostgreSQL Database")
        
        # Test with non-existent name
        config = self.config_manager.get_config_by_name("Non-existent Database")
        self.assertIsNone(config)

    def test_add_config(self):
        """Test adding a new configuration."""
        new_config_dict = {
            "id": "db3",
            "name": "Test SQLite Database",
            "db_type": "sqlite",
            "connection_string": "sqlite:///test.db",
            "is_enabled": True,
            "is_read_only": False
        }
        new_config = DBConfig.from_dict(new_config_dict)
        
        # Add the new config
        self.config_manager.add_config(new_config)
        
        # Verify _save_configs was called
        self.config_manager._save_configs.assert_called_once()
        
        # Verify the config was added to the internal list
        added_config = self.config_manager.get_config_by_id("db3")
        self.assertIsNotNone(added_config)
        self.assertEqual(added_config.name, "Test SQLite Database")

    def test_update_config(self):
        """Test updating an existing configuration."""
        # Get the first config
        config = self.config_manager.get_config_by_id("db1")
        
        # Update some properties
        config.name = "Updated Database Name"
        config.is_enabled = False
        
        # Update the config in the manager
        self.config_manager.update_config(config)
        
        # Verify _save_configs was called
        self.config_manager._save_configs.assert_called_once()
        
        # Verify the config was updated
        updated_config = self.config_manager.get_config_by_id("db1")
        self.assertEqual(updated_config.name, "Updated Database Name")
        self.assertFalse(updated_config.is_enabled)

    def test_delete_config(self):
        """Test deleting a configuration."""
        # Delete the first config
        self.config_manager.delete_config("db1")
        
        # Verify _save_configs was called
        self.config_manager._save_configs.assert_called_once()
        
        # Verify the config was deleted
        deleted_config = self.config_manager.get_config_by_id("db1")
        self.assertIsNone(deleted_config)
        
        # Verify we still have the second config
        remaining_config = self.config_manager.get_config_by_id("db2")
        self.assertIsNotNone(remaining_config)


if __name__ == '__main__':
    unittest.main() 