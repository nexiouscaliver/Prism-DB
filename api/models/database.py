"""
Database models for PrismDB API.

These models define the request and response structures for database operations.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DatabaseInfo(BaseModel):
    """Basic database information"""
    id: str = Field(..., description="Database identifier")
    name: str = Field(..., description="User-friendly name")
    type: str = Field(..., description="Database type (postgres, mysql, etc.)")
    readonly: bool = Field(False, description="Whether the database is read-only")


class DatabaseResponse(BaseModel):
    """Response model for database operations"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class ColumnInfo(BaseModel):
    """Column information"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type")
    nullable: bool = Field(..., description="Whether the column is nullable")
    default: Optional[str] = Field(None, description="Default value")


class ForeignKeyInfo(BaseModel):
    """Foreign key information"""
    columns: List[str] = Field(..., description="Columns in the foreign key")
    referred_table: str = Field(..., description="Referenced table")
    referred_columns: List[str] = Field(..., description="Referenced columns")


class TableInfo(BaseModel):
    """Table information"""
    name: str = Field(..., description="Table name")
    columns: List[ColumnInfo] = Field(..., description="Columns")
    primary_key_columns: List[str] = Field(..., description="Primary key columns")
    foreign_keys: List[ForeignKeyInfo] = Field(..., description="Foreign keys")


class SchemaInfo(BaseModel):
    """Schema information"""
    tables: List[TableInfo] = Field(..., description="Tables")
    database_id: str = Field(..., description="Database identifier")
    database_name: str = Field(..., description="Database name")
    database_type: str = Field(..., description="Database type")


class SchemaResponse(BaseModel):
    """Response model for schema operations"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Optional[SchemaInfo] = Field(None, description="Schema data")


class DatabaseSelectionRequest(BaseModel):
    """Request model for database selection"""
    db_id: str = Field(..., description="Database identifier to select")


class DatabaseSelectionResponse(BaseModel):
    """Response model for database selection"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Optional[DatabaseInfo] = Field(None, description="Selected database")


class SchemaExtractionData(BaseModel):
    """Data model for schema extraction response"""
    source_db: str = Field(..., description="Source database identifier")
    table_count: int = Field(..., description="Number of tables extracted")


class SchemaExtractionResponse(BaseModel):
    """Response model for schema extraction operations"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Optional[SchemaExtractionData] = Field(None, description="Extraction data") 