"""
Response models for PrismDB API.

This module defines all response models used by the PrismDB API,
including query results, visualization data, and error responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Error codes for PrismDB API responses."""
    
    # General errors
    INTERNAL_ERROR = "internal_error"
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    
    # Database connection errors
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    
    # Query execution errors
    QUERY_SYNTAX_ERROR = "query_syntax_error"
    QUERY_EXECUTION_ERROR = "query_execution_error"
    QUERY_TIMEOUT = "query_timeout"
    
    # Natural language to SQL errors
    NL_PARSING_ERROR = "nl_parsing_error"
    SQL_GENERATION_ERROR = "sql_generation_error"
    CONTEXT_ERROR = "context_error"
    
    # Visualization errors
    CHART_DATA_ERROR = "chart_data_error"
    CHART_GENERATION_ERROR = "chart_generation_error"
    CHART_CONVERSION_ERROR = "chart_conversion_error"
    INVALID_CHART_TYPE = "invalid_chart_type"
    INVALID_OUTPUT_FORMAT = "invalid_output_format"


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    message: str = Field(..., description="Human-readable error message")
    code: ErrorCode = Field(..., description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class Column(BaseModel):
    """Database column information."""
    
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    display_name: Optional[str] = Field(None, description="User-friendly display name")


class QueryResult(BaseModel):
    """SQL query execution result."""
    
    columns: List[Column] = Field(..., description="Column definitions for the result")
    rows: List[Dict[str, Any]] = Field(..., description="Result rows as dictionaries")
    execution_time: float = Field(..., description="Query execution time in seconds")
    row_count: int = Field(..., description="Total number of rows returned")
    truncated: bool = Field(False, description="Whether the result was truncated")
    sql: Optional[str] = Field(None, description="The executed SQL query")
    cache_hit: Optional[bool] = Field(None, description="Whether result was served from cache")


class SQLGenerationInfo(BaseModel):
    """Information about the SQL generation process."""
    
    prompt: str = Field(..., description="Original natural language prompt")
    generated_sql: str = Field(..., description="Generated SQL query")
    confidence: float = Field(..., description="Confidence score for the generated SQL")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the generated SQL")
    alternative_queries: Optional[List[str]] = Field(None, description="Alternative SQL queries")


class ChartData(BaseModel):
    """Chart data for visualizations."""
    
    chart_type: str = Field(..., description="Type of chart (bar, line, scatter, etc.)")
    format: str = Field(..., description="Output format (svg, png, json, html, markdown)")
    content_type: str = Field(..., description="MIME type of the content")
    content: Any = Field(..., description="Chart content in the specified format")
    config: Dict[str, Any] = Field(..., description="Chart configuration used")


class ChartSuggestion(BaseModel):
    """Suggested visualization for a query result."""
    
    chart_type: str = Field(..., description="Suggested chart type")
    config: Dict[str, Any] = Field(..., description="Suggested chart configuration")
    explanation: Optional[str] = Field(None, description="Explanation for why this chart is suggested")


class DatabaseInfo(BaseModel):
    """Information about a database connection."""
    
    id: str = Field(..., description="Unique identifier for the database connection")
    name: str = Field(..., description="User-friendly name for the database")
    type: str = Field(..., description="Database type (postgres, mysql, etc.)")
    connection_status: str = Field(..., description="Current connection status")
    tables: Optional[List[str]] = Field(None, description="Available tables in the database")


class QueryResponse(BaseModel):
    """Complete response for a query execution."""
    
    result: Optional[QueryResult] = Field(None, description="Query execution result")
    sql_info: Optional[SQLGenerationInfo] = Field(None, description="Information about SQL generation")
    chart_suggestions: Optional[List[ChartSuggestion]] = Field(None, description="Suggested visualizations")
    chart: Optional[ChartData] = Field(None, description="Generated visualization if requested")
    error: Optional[ErrorResponse] = Field(None, description="Error information if query failed")


class HealthStatus(BaseModel):
    """API health status information."""
    
    status: str = Field(..., description="Overall status (healthy, degraded, unhealthy)")
    version: str = Field(..., description="API version")
    components: Dict[str, str] = Field(..., description="Component statuses")
    uptime: float = Field(..., description="API uptime in seconds") 