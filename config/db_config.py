"""
Database configuration module for PrismDB.

This module provides classes for managing database configurations,
including loading, storing, and validating connection details.
"""

class DBConfig:
    """
    Represents a database configuration with connection details and metadata.
    """
    
    def __init__(self, id, name, db_type, connection_string, is_enabled=True, is_read_only=False):
        """
        Initialize a new DBConfig instance.
        
        Args:
            id (str): Unique identifier for this database configuration
            name (str): Human-readable name for the database
            db_type (str): Type of database (postgresql, mysql, etc.)
            connection_string (str): Database connection string
            is_enabled (bool): Whether this configuration is active
            is_read_only (bool): Whether this connection should be read-only
        """
        self.id = id
        self.name = name
        self.db_type = db_type
        self.connection_string = connection_string
        self.is_enabled = is_enabled
        self.is_read_only = is_read_only
    
    @classmethod
    def from_dict(cls, config_dict):
        """
        Create a DBConfig instance from a dictionary.
        
        Args:
            config_dict (dict): Dictionary containing configuration data
            
        Returns:
            DBConfig: A new DBConfig instance
        """
        return cls(
            id=config_dict["id"],
            name=config_dict["name"],
            db_type=config_dict["db_type"],
            connection_string=config_dict["connection_string"],
            is_enabled=config_dict.get("is_enabled", True),
            is_read_only=config_dict.get("is_read_only", False)
        )
    
    def to_dict(self):
        """
        Convert this DBConfig to a dictionary.
        
        Returns:
            dict: Dictionary representation of this config
        """
        return {
            "id": self.id,
            "name": self.name,
            "db_type": self.db_type,
            "connection_string": self.connection_string,
            "is_enabled": self.is_enabled,
            "is_read_only": self.is_read_only
        }


class DBConfigManager:
    """
    Manages a collection of database configurations.
    
    This class handles loading, saving, and managing database configurations.
    It provides methods to add, update, delete, and retrieve configurations.
    """
    
    def __init__(self):
        """Initialize a new DBConfigManager instance."""
        self.configs = self._load_configs()
    
    def _load_configs(self):
        """
        Load database configurations from storage.
        
        Returns:
            list: List of DBConfig objects
        """
        # This is a stub that would normally load from file or database
        return []
    
    def _save_configs(self):
        """Save the current configurations to storage."""
        # This is a stub that would normally save to file or database
        pass
    
    def get_all_configs(self):
        """
        Get all database configurations.
        
        Returns:
            list: List of DBConfig objects
        """
        return self.configs
    
    def get_config_by_id(self, config_id):
        """
        Get a database configuration by ID.
        
        Args:
            config_id (str): ID of the configuration to retrieve
            
        Returns:
            DBConfig or None: The matching configuration or None if not found
        """
        for config in self.configs:
            if config.id == config_id:
                return config
        return None
    
    def get_config_by_name(self, name):
        """
        Get a database configuration by name.
        
        Args:
            name (str): Name of the configuration to retrieve
            
        Returns:
            DBConfig or None: The matching configuration or None if not found
        """
        for config in self.configs:
            if config.name == name:
                return config
        return None
    
    def add_config(self, config):
        """
        Add a new database configuration.
        
        Args:
            config (DBConfig): Configuration to add
        """
        self.configs.append(config)
        self._save_configs()
    
    def update_config(self, config):
        """
        Update an existing database configuration.
        
        Args:
            config (DBConfig): Updated configuration
        """
        for i, existing_config in enumerate(self.configs):
            if existing_config.id == config.id:
                self.configs[i] = config
                break
        self._save_configs()
    
    def delete_config(self, config_id):
        """
        Delete a database configuration.
        
        Args:
            config_id (str): ID of the configuration to delete
        """
        self.configs = [c for c in self.configs if c.id != config_id]
        self._save_configs() 