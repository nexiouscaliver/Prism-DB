"""
Authentication controllers for PrismDB.

This module handles the business logic for user authentication, JWT token 
generation, validation, and revocation using Redis for token storage.
"""
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any, Tuple, Optional
import asyncio

from flask import current_app, jsonify
from flask_jwt_extended import (
    create_access_token, 
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
)
from werkzeug.security import check_password_hash
from pydantic import BaseModel, Field, EmailStr
import redis.asyncio as redis
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app import db, logger

# Define error codes for authentication failures
class AuthErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID" 
    TOKEN_REVOKED = "TOKEN_REVOKED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class AuthRequest(BaseModel):
    """Pydantic model for authentication request validation."""
    
    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class TokenResponse(BaseModel):
    """Pydantic model for token response."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    expires_at: int = Field(..., description="Access token expiry timestamp")
    token_type: str = Field("Bearer", description="Token type")


# Redis client for token storage
redis_client = None
redis_is_available = True


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((redis.ConnectionError, redis.TimeoutError))
)
async def get_redis_client() -> Optional[redis.Redis]:
    """Get or create a Redis client with circuit breaker pattern.
    
    Returns:
        Redis client if available, None otherwise
    """
    global redis_client, redis_is_available
    
    if not redis_is_available:
        # If Redis was previously marked as unavailable, check if we should retry
        current_time = datetime.utcnow()
        last_check = getattr(get_redis_client, 'last_check', datetime.min)
        if (current_time - last_check).total_seconds() < 60:  # Check once per minute
            return None
        get_redis_client.last_check = current_time
    
    try:
        if redis_client is None:
            redis_url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
            redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            # Test connection
            await redis_client.ping()
        redis_is_available = True
        return redis_client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        redis_is_available = False
        logger.error(f"Redis connection error: {str(e)}")
        return None


async def store_token_fingerprint(user_id: str, token_id: str, is_refresh: bool = False) -> None:
    """Store token fingerprint in Redis with user role and permissions.
    
    Args:
        user_id: User ID
        token_id: Unique token identifier
        is_refresh: Whether this is a refresh token
    """
    r = await get_redis_client()
    if not r:
        logger.warning("Redis unavailable, skipping token fingerprint storage")
        return
    
    try:
        # Get user details from database
        # In a real implementation, this would query the database
        # For demo purposes, we're using hardcoded values
        user_role = "analyst"  # Would be fetched from database
        user_prisms = ["sales_db::read", "inventory_db::write"]  # Would be fetched from database
        
        # Store token information
        key = f"token:{token_id}"
        expiry = 60 * 60 * 24 * 7 if is_refresh else 60 * 60  # 7 days or 1 hour
        
        token_data = {
            "user_id": user_id,
            "role": user_role,
            "prisms": user_prisms,
            "is_refresh": is_refresh,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store as JSON string since we're using redis.asyncio which doesn't have built-in JSON support
        await r.set(key, json.dumps(token_data))
        await r.expire(key, expiry)
    except Exception as e:
        logger.error(f"Error storing token fingerprint: {str(e)}")
        # Continue execution - token will work but won't be revocable


async def revoke_token(token_id: str) -> bool:
    """Revoke a token by deleting it from Redis.
    
    Args:
        token_id: Token ID to revoke
        
    Returns:
        True if token was found and revoked, False otherwise
    """
    r = await get_redis_client()
    if not r:
        logger.warning("Redis unavailable, cannot revoke token")
        return False
    
    try:
        key = f"token:{token_id}"
        
        # Check if token exists
        if not await r.exists(key):
            return False
        
        # Delete token
        await r.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        return False


async def is_token_valid(token_id: str) -> bool:
    """Check if a token is valid (exists in Redis).
    
    Args:
        token_id: Token ID to check
        
    Returns:
        True if token is valid, False otherwise
        If Redis is unavailable, returns True to prevent blocking authentication
    """
    r = await get_redis_client()
    if not r:
        logger.warning("Redis unavailable, assuming token is valid")
        return True  # Assume token is valid if Redis is down (graceful degradation)
    
    try:
        key = f"token:{token_id}"
        return await r.exists(key) == 1
    except Exception as e:
        logger.error(f"Error checking token validity: {str(e)}")
        return True  # Assume token is valid in case of error


async def get_token_data(token_id: str) -> Optional[Dict[str, Any]]:
    """Get token data from Redis.
    
    Args:
        token_id: Token ID to get data for
        
    Returns:
        Token data dictionary if found, None otherwise
    """
    r = await get_redis_client()
    if not r:
        logger.warning("Redis unavailable, cannot get token data")
        return None
    
    try:
        key = f"token:{token_id}"
        
        if await r.exists(key) != 1:
            return None
        
        data = await r.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Error getting token data: {str(e)}")
        return None


async def check_rate_limit(user_id: str) -> Tuple[bool, int]:
    """Check if user has exceeded rate limit.
    
    Args:
        user_id: User ID to check
        
    Returns:
        Tuple of (is_limited, requests_remaining)
        If Redis is unavailable, returns (False, max_requests)
    """
    r = await get_redis_client()
    max_requests = 10  # 10 requests per minute
    
    if not r:
        logger.warning("Redis unavailable, skipping rate limiting")
        return False, max_requests  # Skip rate limiting if Redis is down
    
    try:
        key = f"ratelimit:{user_id}"
        window = 60  # 1 minute window
        
        # Get current count
        count = await r.get(key)
        count = int(count) if count else 0
        
        if count >= max_requests:
            # User has exceeded rate limit
            ttl = await r.ttl(key)
            return True, ttl
        
        # Increment count and set expiry if not exists
        pipeline = r.pipeline()
        await pipeline.incr(key)
        
        # Set expiry only if it doesn't exist
        if count == 0:
            await pipeline.expire(key, window)
        
        await pipeline.execute()
        
        return False, max_requests - count - 1
    except Exception as e:
        logger.error(f"Error checking rate limit: {str(e)}")
        return False, max_requests  # Skip rate limiting in case of error


async def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Tuple of (success, user_data, error_code)
    """
    # In a real implementation, this would query the database
    # For demo purposes, we're using hardcoded values
    if username == "demo" and password == "demo_password":
        return True, {
            "id": "user_123",
            "username": username,
            "role": "analyst",
            "prisms": ["sales_db::read", "inventory_db::write"]
        }, None
    
    return False, None, AuthErrorCode.INVALID_CREDENTIALS


async def generate_tokens(user_id: str) -> Dict[str, Any]:
    """Generate access and refresh tokens for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with access and refresh tokens
    """
    # Generate unique IDs for tokens
    access_token_id = str(uuid.uuid4())
    refresh_token_id = str(uuid.uuid4())
    
    # Get user details
    # In a real implementation, this would query the database
    user_role = "analyst"  # Would be fetched from database
    user_prisms = ["sales_db::read", "inventory_db::write"]  # Would be fetched from database
    
    # Create JWT claims
    access_claims = {
        "sub": user_id,
        "prisms": user_prisms,
        "role": user_role,
        "type": "access",
        "jti": access_token_id
    }
    
    refresh_claims = {
        "sub": user_id,
        "type": "refresh",
        "jti": refresh_token_id
    }
    
    # Create tokens
    access_expires = timedelta(hours=1)
    refresh_expires = timedelta(days=7)
    
    access_token = create_access_token(
        identity=user_id, 
        additional_claims=access_claims,
        expires_delta=access_expires
    )
    
    refresh_token = create_refresh_token(
        identity=user_id,
        additional_claims=refresh_claims,
        expires_delta=refresh_expires
    )
    
    # Store token fingerprints in Redis
    await store_token_fingerprint(user_id, access_token_id)
    await store_token_fingerprint(user_id, refresh_token_id, is_refresh=True)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int((datetime.utcnow() + access_expires).timestamp()),
        "token_type": "Bearer"
    } 