"""
Execution service for PrismDB.

This service provides an abstraction layer for executing SQL queries
against various database engines, with built-in retry logic and
result caching using Redis.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import redis.asyncio as redis
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import settings
from models.response_models import Column, ErrorCode, ErrorResponse, QueryResult


logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Service for executing SQL queries with retry logic and result caching.
    
    This service handles:
    - Connection management to various database engines
    - SQL query execution with configurable timeouts and retries
    - Result caching via Redis
    - Error handling and standardized responses
    """
    
    def __init__(self):
        """Initialize the execution service with a Redis client for caching."""
        self.engines: Dict[str, Engine] = {}
        self.redis_client = None
        
        if settings.CACHE_ENABLED:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis cache connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self.redis_client = None
    
    async def initialize(self):
        """Initialize connections and perform startup checks."""
        # Initialize configured database connections
        for db_config in settings.DATABASES:
            self.add_engine(db_config["id"], db_config["connection_string"])
        
        # Test Redis connection
        if self.redis_client:
            try:
                await self.redis_client.ping()
                logger.info("Redis connection verified")
            except Exception as e:
                logger.error(f"Redis connection test failed: {str(e)}")
                self.redis_client = None
    
    def add_engine(self, db_id: str, connection_string: str) -> None:
        """
        Add a database engine to the service.
        
        Args:
            db_id: Unique identifier for the database connection
            connection_string: SQLAlchemy connection string
        """
        try:
            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.SQL_DEBUG,
            )
            self.engines[db_id] = engine
            logger.info(f"Added database engine: {db_id}")
        except Exception as e:
            logger.error(f"Failed to create engine for {db_id}: {str(e)}")
            raise
    
    def remove_engine(self, db_id: str) -> None:
        """
        Remove a database engine from the service.
        
        Args:
            db_id: Unique identifier for the database connection
        """
        if db_id in self.engines:
            engine = self.engines.pop(db_id)
            engine.dispose()
            logger.info(f"Removed database engine: {db_id}")
    
    def _generate_cache_key(self, db_id: str, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a cache key for a query.
        
        Args:
            db_id: Database identifier
            query: SQL query string
            params: Query parameters
            
        Returns:
            Unique cache key for the query
        """
        # Create a serializable representation of the query and params
        query_data = {
            "db_id": db_id,
            "query": query,
            "params": params or {}
        }
        
        # Generate a deterministic hash
        serialized = json.dumps(query_data, sort_keys=True)
        hash_obj = hashlib.sha256(serialized.encode())
        return f"prismdb:query:{hash_obj.hexdigest()}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached query result.
        
        Args:
            cache_key: Unique cache key for the query
            
        Returns:
            Cached result as a dict or None if not found
        """
        if not self.redis_client or not settings.CACHE_ENABLED:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error: {str(e)}")
            return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any], ttl: int = None) -> bool:
        """
        Cache a query result.
        
        Args:
            cache_key: Unique cache key for the query
            result: Query result to cache
            ttl: Time-to-live in seconds (defaults to CACHE_TTL from settings)
            
        Returns:
            Boolean indicating if caching was successful
        """
        if not self.redis_client or not settings.CACHE_ENABLED:
            return False
        
        ttl = ttl or settings.CACHE_TTL
        
        try:
            serialized = json.dumps(result)
            await self.redis_client.setex(cache_key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache storage error: {str(e)}")
            return False
    
    async def _invalidate_cache_for_db(self, db_id: str) -> None:
        """
        Invalidate all cached queries for a specific database.
        
        Args:
            db_id: Database identifier
        """
        if not self.redis_client:
            return
        
        try:
            # Find all keys matching the pattern for this database
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, 
                    match=f"prismdb:query:*", 
                    count=100
                )
                
                if keys:
                    # For each key, check if it's for this database before deleting
                    for key in keys:
                        cached_data = await self.redis_client.get(key)
                        if cached_data:
                            try:
                                data = json.loads(cached_data)
                                if data.get("db_id") == db_id:
                                    await self.redis_client.delete(key)
                            except json.JSONDecodeError:
                                continue
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated cache for database: {db_id}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
    
    @retry(
        retry=retry_if_exception_type(SQLAlchemyError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def _execute_query(
        self, 
        db_id: str, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        timeout: int = None
    ) -> Tuple[List[Dict[str, Any]], List[Column], float]:
        """
        Execute a SQL query with retry logic.
        
        Args:
            db_id: Database identifier
            query: SQL query string
            params: Query parameters
            timeout: Query timeout in seconds
            
        Returns:
            Tuple of (rows, columns, execution_time)
            
        Raises:
            ValueError: If database engine is not found
            SQLAlchemyError: On database errors after retries
        """
        if db_id not in self.engines:
            raise ValueError(f"Database engine not found: {db_id}")
        
        engine = self.engines[db_id]
        timeout = timeout or settings.QUERY_TIMEOUT
        start_time = time.time()
        
        # Execute query using a thread executor since SQLAlchemy doesn't support asyncio natively
        loop = asyncio.get_event_loop()
        
        def execute_in_thread():
            with engine.connect() as connection:
                # Set statement timeout if supported by the dialect
                if hasattr(connection, "execution_options"):
                    connection = connection.execution_options(timeout=timeout)
                
                result = connection.execute(text(query), params or {})
                columns = [
                    Column(
                        name=col.name,
                        type=str(col.type),
                        display_name=col.name.replace("_", " ").title()
                    )
                    for col in result.cursor.description
                ]
                
                # Convert to list of dicts while in the thread to avoid cursor issues
                rows = [dict(row) for row in result]
                return rows, columns
        
        try:
            rows, columns = await loop.run_in_executor(None, execute_in_thread)
            execution_time = time.time() - start_time
            return rows, columns, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution error after {execution_time:.2f}s: {str(e)}")
            raise
    
    async def execute_query(
        self,
        db_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = None,
        max_rows: int = None,
        use_cache: bool = True,
        cache_ttl: int = None
    ) -> Union[QueryResult, ErrorResponse]:
        """
        Execute a SQL query with caching and error handling.
        
        Args:
            db_id: Database identifier
            query: SQL query string
            params: Query parameters
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds
            
        Returns:
            QueryResult on success or ErrorResponse on failure
        """
        max_rows = max_rows or settings.MAX_ROWS
        cache_key = None
        
        if use_cache and settings.CACHE_ENABLED:
            cache_key = self._generate_cache_key(db_id, query, params)
            cached_result = await self._get_cached_result(cache_key)
            
            if cached_result:
                logger.info(f"Cache hit for query on {db_id}")
                result = QueryResult(**cached_result)
                result.cache_hit = True
                return result
        
        try:
            rows, columns, execution_time = await self._execute_query(
                db_id=db_id,
                query=query,
                params=params,
                timeout=timeout
            )
            
            # Apply row limit if needed
            truncated = False
            if max_rows and len(rows) > max_rows:
                rows = rows[:max_rows]
                truncated = True
            
            # Process data types (convert datetime objects to ISO strings, etc.)
            for row in rows:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            
            result = QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time=execution_time,
                truncated=truncated,
                sql=query,
                cache_hit=False
            )
            
            # Cache the result if enabled
            if use_cache and settings.CACHE_ENABLED and cache_key:
                # We need to convert to dict for caching
                result_dict = result.dict(exclude={"cache_hit"})
                await self._cache_result(cache_key, result_dict, cache_ttl)
            
            return result
            
        except ValueError as e:
            return ErrorResponse(
                message=f"Database error: {str(e)}",
                code=ErrorCode.CONNECTION_ERROR
            )
        except SQLAlchemyError as e:
            return ErrorResponse(
                message=f"Query execution error: {str(e)}",
                code=ErrorCode.QUERY_EXECUTION_ERROR,
                details={"error": str(e)}
            )
        except asyncio.TimeoutError:
            return ErrorResponse(
                message=f"Query timed out after {timeout} seconds",
                code=ErrorCode.QUERY_TIMEOUT
            )
        except Exception as e:
            logger.exception("Unexpected error during query execution")
            return ErrorResponse(
                message=f"Internal server error: {str(e)}",
                code=ErrorCode.INTERNAL_ERROR,
                details={"error": str(e)}
            )


# Create singleton instance
execution_service = ExecutionService() 