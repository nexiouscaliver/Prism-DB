import functools
from typing import Callable, Dict, List, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time
import os
from datetime import datetime, timedelta

# For demo purposes, we'll use a simple in-memory store for tokens
# In a real app, you'd use a database
TOKENS = {}
USERS = [
    {"id": "1", "username": "admin", "email": "admin@prismdb.io", "password": "admin123"},
    {"id": "2", "username": "user", "email": "user@prismdb.io", "password": "user123"}
]

# Generate a secret key for JWT tokens
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "prismdb-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 1 day

security = HTTPBearer()

def create_token(user_id: str, username: str, email: str) -> str:
    """Create a JWT token for a user"""
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token: str) -> Optional[Dict]:
    """Verify a JWT token and return the payload if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def apply_auth_middleware(app: FastAPI):
    """Apply authentication middleware to a FastAPI app"""
    
    # Authentication routes
    @app.post("/api/auth/login")
    async def login(credentials: dict):
        username = credentials.get("username")
        password = credentials.get("password")
        
        # Find user by credentials
        user = next((u for u in USERS if u["username"] == username and u["password"] == password), None)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create token
        token = create_token(user["id"], user["username"], user["email"])
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    
    @app.post("/api/auth/register")
    async def register(user_data: dict):
        username = user_data.get("username")
        email = user_data.get("email")
        password = user_data.get("password")
        
        # Check if username or email already exists
        existing_user = next((u for u in USERS if u["username"] == username or u["email"] == email), None)
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Create new user
        new_user = {
            "id": str(len(USERS) + 1),
            "username": username,
            "email": email,
            "password": password
        }
        
        USERS.append(new_user)
        
        # Create token
        token = create_token(new_user["id"], new_user["username"], new_user["email"])
        
        return {
            "token": token,
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"]
            }
        }
    
    # Middleware to check authentication for protected routes
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next: Callable) -> Response:
        # Skip auth for login and register routes
        if request.url.path in ["/api/auth/login", "/api/auth/register"]:
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # For now, we'll allow requests without auth to pass through
            # This is to maintain compatibility with the current frontend
            # In a real app, you would return a 401 here
            return await call_next(request)
        
        token = auth_header.replace("Bearer ", "")
        payload = verify_token(token)
        
        if not payload:
            # For now, we'll allow requests with invalid auth to pass through
            # This is to maintain compatibility with the current frontend
            # In a real app, you would return a 401 here
            return await call_next(request)
        
        # Attach user info to request state
        request.state.user = payload
        
        return await call_next(request)
    
    return app 