"""
Multi-Database Configuration for PrismDB.

This module handles the configuration and management of multiple database connections
using environment variables or other configuration sources.
"""
from typing import Dict, List, Optional, Any, Union
import os
from pydantic import BaseModel, Field, validator
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class DatabaseConfig(BaseModel):
    """Configuration for a database connection."""
    
    id: str = Field(..., description="Unique identifier for this database")
    name: str = Field(..., description="User-friendly name for this database")
    connection_string: str = Field(..., description="SQLAlchemy connection string")
    type: str = Field(..., description="Database type (postgres, mysql, etc.)")
    enabled: bool = Field(True, description="Whether this database is enabled")
    readonly: bool = Field(False, description="Whether this database is read-only")
    
    class Config:
        extra = "ignore"


def load_database_configs() -> List[DatabaseConfig]:
    """Load database configurations from environment variables."""
    configs = []
    
    # Load the default database from DATABASE_URL
    default_db = os.environ.get("DATABASE_URL")
    if default_db:
        configs.append(DatabaseConfig(
            id="default",
            name="Default Database",
            connection_string=default_db,
            type=_detect_db_type(default_db),
        ))
    
    # Look for additional numbered databases (DATABASE_1_URL, DATABASE_2_URL, etc.)
    db_index = 1
    while True:
        db_url = os.environ.get(f"DATABASE_{db_index}_URL")
        if not db_url:
            break
            
        db_name = os.environ.get(f"DATABASE_{db_index}_NAME", f"Database {db_index}")
        db_type = os.environ.get(f"DATABASE_{db_index}_TYPE") or _detect_db_type(db_url)
        db_enabled = os.environ.get(f"DATABASE_{db_index}_ENABLED", "true").lower() == "true"
        db_readonly = os.environ.get(f"DATABASE_{db_index}_READONLY", "false").lower() == "true"
        
        configs.append(DatabaseConfig(
            id=f"db_{db_index}",
            name=db_name,
            connection_string=db_url,
            type=db_type,
            enabled=db_enabled,
            readonly=db_readonly,
        ))
        
        logger.info(f"Loaded database configuration: {db_name} (ID: db_{db_index}, Type: {db_type})")
        db_index += 1
    
    # Also look for JSON configuration from DATABASE_CONFIG env var
    db_config_json = os.environ.get("DATABASE_CONFIG")
    if db_config_json:
        try:
            db_configs = json.loads(db_config_json)
            for config in db_configs:
                # Skip if ID is already in configs
                if any(db.id == config.get("id") for db in configs):
                    continue
                    
                configs.append(DatabaseConfig(
                    id=config.get("id"),
                    name=config.get("name"),
                    connection_string=config.get("connection_string"),
                    type=config.get("type", _detect_db_type(config.get("connection_string"))),
                    enabled=config.get("enabled", True),
                    readonly=config.get("readonly", False),
                ))
                logger.info(f"Loaded database from JSON config: {config.get('name')} (ID: {config.get('id')})")
        except Exception as e:
            logger.error(f"Failed to parse DATABASE_CONFIG JSON: {str(e)}")
    
    if not configs:
        logger.warning("No database configurations found")
    else:
        logger.info(f"Loaded {len(configs)} database configurations")
    
    return configs


def _detect_db_type(connection_string: str) -> str:
    """Detect database type from connection string."""
    if connection_string.startswith("postgresql"):
        return "postgres"
    elif connection_string.startswith("mysql"):
        return "mysql"
    elif connection_string.startswith("sqlite"):
        return "sqlite"
    elif connection_string.startswith("mssql"):
        return "mssql"
    elif connection_string.startswith("oracle"):
        return "oracle"
    else:
        return "unknown"


# Export database configurations
DATABASES = load_database_configs()

def get_db_config(db_id: str = "default") -> Optional[DatabaseConfig]:
    """Get database configuration by ID.
    
    Args:
        db_id: The database identifier.
        
    Returns:
        The database configuration or None if not found.
    """
    for config in DATABASES:
        if config.id == db_id and config.enabled:
            return config
    return None

def get_all_db_configs(include_disabled: bool = False) -> List[Dict[str, Any]]:
    """Get information about all databases.
    
    Args:
        include_disabled: Whether to include disabled databases.
        
    Returns:
        List of database information dictionaries.
    """
    result = []
    for config in DATABASES:
        if include_disabled or config.enabled:
            result.append({
                "id": config.id,
                "name": config.name,
                "type": config.type,
                "readonly": config.readonly,
                "enabled": config.enabled
            })
    return result 