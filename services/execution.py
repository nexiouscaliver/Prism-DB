"""
SQL execution service for PrismDB.

This module handles the execution of SQL queries against databases,
with support for retrying failed queries, caching results in Redis,
and handling various database connection types.
"""

import asyncio
import time
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta

import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import text
import redis.asyncio as redis
import pandas as pd
import numpy as np

from models.response_models import (
    ErrorCode,
    create_error_response,
    create_query_response,
    QueryResultColumn
)
from config import settings


# Configure logging
logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Service for executing SQL queries against databases with caching.
    
    Features:
    - Asynchronous execution of SQL queries
    - Connection pooling and reuse
    - Automatic retries for transient errors
    - Result caching in Redis
    - Support for multiple database types
    - Query timeout enforcement
    - Parameterized queries
    """
    
    def __init__(self, connection_string: str = None, redis_url: str = None):
        """
        Initialize the execution service.
        
        Args:
            connection_string: Database connection string
            redis_url: Redis connection URL for caching
        """
        self.connection_string = connection_string or settings.DATABASE_URL
        self.redis_url = redis_url or settings.REDIS_URL
        self.engine = None
        self.redis_client = None
        self.is_initialized = False
        self.dialect = None
        self.max_retries = settings.DATABASE_MAX_RETRIES
        self.retry_delay = settings.DATABASE_RETRY_DELAY
        self.default_timeout = settings.DATABASE_QUERY_TIMEOUT
        self.default_cache_ttl = settings.CACHE_DEFAULT_TTL
    
    async def initialize(self):
        """Initialize database and Redis connections."""
        if self.is_initialized:
            return
        
        # Create async SQLAlchemy engine
        try:
            self.engine = create_async_engine(
                self.connection_string,
                echo=settings.DATABASE_ECHO_SQL,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                pool_recycle=settings.DATABASE_POOL_RECYCLE,
                pool_pre_ping=True,
            )
            
            # Determine SQL dialect
            self.dialect = self.engine.dialect.name
            logger.info(f"Connected to {self.dialect} database")
            
            # Initialize Redis connection
            if self.redis_url:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test Redis connection
                await self.redis_client.ping()
                logger.info("Connected to Redis cache")
            
            self.is_initialized = True
        
        except Exception as e:
            logger.error(f"Failed to initialize execution service: {str(e)}")
            raise
    
    async def close(self):
        """Close database and Redis connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Closed database connection")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Closed Redis connection")
        
        self.is_initialized = False
    
    def _generate_cache_key(self, sql: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key from SQL query and parameters.
        
        Args:
            sql: The SQL query string
            params: Query parameters
            
        Returns:
            A unique cache key string
        """
        # Create a string containing SQL and parameters
        key_parts = [sql]
        if params:
            # Sort parameters by key to ensure consistent order
            for k in sorted(params.keys()):
                key_parts.append(f"{k}:{params[k]}")
        
        # Join and hash the key parts
        key_str = "|".join(key_parts)
        hash_obj = hashlib.md5(key_str.encode())
        query_hash = hash_obj.hexdigest()
        
        return f"query:{query_hash}"
    
    async def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query result from Redis.
        
        Args:
            cache_key: The cache key to retrieve
            
        Returns:
            The cached result or None if not found/expired
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"Cache hit for key: {cache_key}")
                return result
            
            logger.info(f"Cache miss for key: {cache_key}")
            return None
        
        except Exception as e:
            logger.warning(f"Error retrieving cached result: {str(e)}")
            return None
    
    async def cache_result(
        self, 
        cache_key: str, 
        result: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache query result in Redis.
        
        Args:
            cache_key: The cache key
            result: The result to cache
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            True if caching was successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        ttl = ttl or self.default_cache_ttl
        
        try:
            # Convert result to JSON string
            result_json = json.dumps(result)
            
            # Store in Redis with expiration
            await self.redis_client.setex(
                cache_key, 
                ttl,
                result_json
            )
            
            logger.info(f"Cached result with key {cache_key} (TTL: {ttl}s)")
            return True
        
        except Exception as e:
            logger.warning(f"Error caching result: {str(e)}")
            return False
    
    async def invalidate_cache(self, pattern: str = "query:*") -> int:
        """
        Invalidate cached query results matching the pattern.
        
        Args:
            pattern: Redis key pattern to match for deletion
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            # Get keys matching the pattern
            keys = await self.redis_client.keys(pattern)
            
            if not keys:
                return 0
            
            # Delete the keys
            deleted = await self.redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")
            return deleted
        
        except Exception as e:
            logger.warning(f"Error invalidating cache: {str(e)}")
            return 0
    
    def _column_info_from_cursor(self, cursor) -> List[Dict[str, Any]]:
        """
        Extract column information from cursor description.
        
        Args:
            cursor: Database cursor with executed query
            
        Returns:
            List of column information dictionaries
        """
        columns = []
        
        for col in cursor.description:
            # Column name is always the first item
            name = col[0]
            
            # Type handling varies by database
            type_code = col[1]
            type_name = "unknown"
            
            # Get type name based on dialect
            if hasattr(type_code, "__name__"):
                type_name = type_code.__name__
            elif hasattr(type_code, "name"):
                type_name = type_code.name
            
            # Nullable status (if available)
            nullable = True
            if len(col) > 6 and col[6] is not None:
                nullable = bool(col[6])
            
            column = {
                "name": name,
                "data_type": type_name,
                "nullable": nullable
            }
            
            columns.append(column)
        
        return columns
    
    async def _format_result(self, cursor, execution_time_ms: int) -> Dict[str, Any]:
        """
        Format query results from cursor into standard response format.
        
        Args:
            cursor: Database cursor with executed query
            execution_time_ms: Query execution time in milliseconds
            
        Returns:
            Formatted query result
        """
        # Get column information
        columns = self._column_info_from_cursor(cursor)
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        # Create list of dictionaries for rows
        result_rows = []
        for row in rows:
            # Convert row to dictionary
            row_dict = {}
            for i, col in enumerate(columns):
                col_name = col["name"]
                value = row[i]
                
                # Handle special data types
                if isinstance(value, (datetime, pd.Timestamp)):
                    value = value.isoformat()
                elif isinstance(value, (np.integer, np.float_, np.bool_)):
                    value = value.item()
                elif pd.isna(value):
                    value = None
                
                row_dict[col_name] = value
            
            result_rows.append(row_dict)
        
        # Build result metadata
        metadata = {
            "execution_time_ms": execution_time_ms,
            "row_count": len(result_rows),
            "column_count": len(columns),
            "cached": False,
            "query_id": str(uuid.uuid4())
        }
        
        # Build complete result
        result = {
            "columns": columns,
            "rows": result_rows
        }
        
        return result, metadata
    
    async def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query with caching and retries.
        
        Args:
            sql: The SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds
            use_cache: Whether to use cache for this query
            cache_ttl: Cache TTL in seconds (None for default)
            
        Returns:
            Query result in standardized format
        """
        if not self.is_initialized:
            await self.initialize()
        
        timeout = timeout or self.default_timeout
        cache_ttl = cache_ttl or self.default_cache_ttl
        
        # Generate cache key
        cache_key = self._generate_cache_key(sql, params)
        
        # Check cache if enabled
        if use_cache and self.redis_client:
            cached_result = await self.get_cached_result(cache_key)
            if cached_result:
                # Update cache metadata
                cached_result["metadata"]["cached"] = True
                return cached_result
        
        # Set timeout
        if timeout:
            timeout_dt = timedelta(seconds=timeout)
        else:
            timeout_dt = None
        
        # Retry logic
        retries = 0
        last_error = None
        
        while retries <= self.max_retries:
            try:
                start_time = time.time()
                
                # Create SQLAlchemy text object with parameters
                if params:
                    # Replace parameter placeholders based on dialect
                    query = text(sql)
                    bind_params = params
                else:
                    query = text(sql)
                    bind_params = {}
                
                # Execute query with timeout
                async with self.engine.connect() as conn:
                    # Create a transaction
                    async with conn.begin():
                        # Execute query with timeout
                        cursor = await asyncio.wait_for(
                            conn.execute(query, bind_params),
                            timeout=timeout
                        )
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Format result
                result, metadata = await self._format_result(cursor, execution_time_ms)
                
                # Add cache information to metadata
                if use_cache and self.redis_client:
                    metadata["cache_key"] = cache_key
                    metadata["cache_ttl"] = cache_ttl
                
                # Create standard response
                response = create_query_response(
                    sql=sql,
                    data=result,
                    metadata=metadata,
                    sql_params=params
                )
                
                # Cache result if enabled
                if use_cache and self.redis_client:
                    await self.cache_result(cache_key, response, cache_ttl)
                
                return response
            
            except asyncio.TimeoutError:
                last_error = "Query execution timed out"
                logger.warning(f"Query timeout after {timeout}s: {sql[:100]}...")
                
                # Don't retry on timeout
                return create_error_response(
                    code=ErrorCode.QUERY_TIMEOUT,
                    message=f"Query execution timed out after {timeout} seconds",
                    details={"sql": sql, "params": params}
                )
            
            except Exception as e:
                retries += 1
                last_error = str(e)
                
                if retries <= self.max_retries:
                    wait_time = self.retry_delay * retries
                    logger.warning(
                        f"Query error (attempt {retries}/{self.max_retries}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries exceeded
                    logger.error(f"Query failed after {self.max_retries} retries: {str(e)}")
        
        # All retries failed
        error_code = ErrorCode.QUERY_EXECUTION_ERROR
        if "connection" in last_error.lower():
            error_code = ErrorCode.DATABASE_CONNECTION_ERROR
        elif "permission" in last_error.lower() or "privilege" in last_error.lower():
            error_code = ErrorCode.DATABASE_PERMISSION_ERROR
        elif "syntax" in last_error.lower():
            error_code = ErrorCode.QUERY_SYNTAX_ERROR
        
        return create_error_response(
            code=error_code,
            message=f"Query execution failed: {last_error}",
            details={"sql": sql, "params": params}
        )
    
    async def execute_metadata_query(self, query_type: str) -> Dict[str, Any]:
        """
        Execute a metadata query to get database schema information.
        
        Args:
            query_type: Type of metadata query (tables, columns, etc.)
            
        Returns:
            Query result with metadata information
        """
        # Get the appropriate query for the database dialect
        if self.dialect == "postgresql":
            if query_type == "tables":
                sql = """
                SELECT 
                    table_schema, 
                    table_name, 
                    table_type
                FROM 
                    information_schema.tables
                WHERE 
                    table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY 
                    table_schema, table_name
                """
            elif query_type == "columns":
                sql = """
                SELECT 
                    table_schema,
                    table_name, 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY 
                    table_schema, table_name, ordinal_position
                """
            else:
                return create_error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"Unknown metadata query type: {query_type}"
                )
        elif self.dialect == "mysql":
            if query_type == "tables":
                sql = """
                SELECT 
                    table_schema,
                    table_name, 
                    table_type
                FROM 
                    information_schema.tables
                WHERE 
                    table_schema NOT IN ('mysql', 'information_schema', 
                                        'performance_schema', 'sys')
                ORDER BY 
                    table_schema, table_name
                """
            elif query_type == "columns":
                sql = """
                SELECT 
                    table_schema,
                    table_name, 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM 
                    information_schema.columns
                WHERE 
                    table_schema NOT IN ('mysql', 'information_schema', 
                                        'performance_schema', 'sys')
                ORDER BY 
                    table_schema, table_name, ordinal_position
                """
            else:
                return create_error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"Unknown metadata query type: {query_type}"
                )
        elif self.dialect in ("sqlite", "sqlite3"):
            if query_type == "tables":
                sql = """
                SELECT 
                    'main' as table_schema, 
                    name as table_name,
                    type as table_type
                FROM 
                    sqlite_master
                WHERE 
                    type IN ('table', 'view')
                    AND name NOT LIKE 'sqlite_%'
                ORDER BY 
                    name
                """
            elif query_type == "columns":
                # SQLite requires dynamic queries for column information
                tables_result = await self.execute_query(
                    """
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' 
                    AND name NOT LIKE 'sqlite_%'
                    """
                )
                
                all_columns = []
                for table in tables_result.get("data", {}).get("rows", []):
                    table_name = table["name"]
                    pragma_sql = f"PRAGMA table_info({table_name})"
                    columns_result = await self.execute_query(pragma_sql)
                    
                    for col in columns_result.get("data", {}).get("rows", []):
                        all_columns.append({
                            "table_schema": "main",
                            "table_name": table_name,
                            "column_name": col["name"],
                            "data_type": col["type"],
                            "is_nullable": "YES" if col["notnull"] == 0 else "NO",
                            "column_default": col["dflt_value"]
                        })
                
                # Create a mock response
                return {
                    "status": "success",
                    "message": "Metadata query executed successfully",
                    "data": {
                        "columns": [
                            {"name": "table_schema", "data_type": "text", "nullable": False},
                            {"name": "table_name", "data_type": "text", "nullable": False},
                            {"name": "column_name", "data_type": "text", "nullable": False},
                            {"name": "data_type", "data_type": "text", "nullable": True},
                            {"name": "is_nullable", "data_type": "text", "nullable": True},
                            {"name": "column_default", "data_type": "text", "nullable": True}
                        ],
                        "rows": all_columns
                    },
                    "metadata": {
                        "execution_time_ms": 0,
                        "row_count": len(all_columns),
                        "column_count": 6,
                        "cached": False,
                        "query_id": str(uuid.uuid4())
                    },
                    "sql": "PRAGMA table_info for multiple tables"
                }
            else:
                return create_error_response(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=f"Unknown metadata query type: {query_type}"
                )
        else:
            return create_error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Unsupported database dialect: {self.dialect}"
            )
        
        # Execute the metadata query
        result = await self.execute_query(sql, use_cache=True, cache_ttl=3600)
        return result


# Global instance for singleton access
_execution_service: Optional[ExecutionService] = None


async def get_execution_service() -> ExecutionService:
    """
    Get the global execution service instance.
    
    Returns:
        ExecutionService instance
    """
    global _execution_service
    
    if _execution_service is None:
        _execution_service = ExecutionService(
            connection_string=settings.DATABASE_URL,
            redis_url=settings.REDIS_URL
        )
        await _execution_service.initialize()
    
    return _execution_service


async def close_execution_service():
    """Close the global execution service instance."""
    global _execution_service
    
    if _execution_service is not None:
        await _execution_service.close()
        _execution_service = None 