"""
Configuration module for PrismDB.

This module manages configuration settings, API keys, and environment variables.
"""
import os
from typing import Dict, Any

# Google API Configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
DEFAULT_MODEL = "gemini-2.0-flash-exp"

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prismdb")

# Application Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-key-change-in-production")
DEBUG = os.environ.get("FLASK_ENV", "development") == "development"

# Model Configuration
MODEL_CONFIG = {
    "gemini-2.0-flash-exp": {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    },
    "gemini-1.5-pro-exp": {
        "temperature": 0.4,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 4096,
    }
}


def get_model_config(model_id: str = None) -> Dict[str, Any]:
    """Get configuration for a specific model.
    
    Args:
        model_id: The model identifier to get configuration for.
            If None, the default model configuration is returned.
            
    Returns:
        Dictionary with model configuration.
    """
    model = model_id or DEFAULT_MODEL
    return MODEL_CONFIG.get(model, MODEL_CONFIG[DEFAULT_MODEL])


def configure_api_keys() -> None:
    """Configure API keys for various services.
    
    This function should be called during application startup.
    It ensures all required API keys are properly set.
    
    Raises:
        ValueError: If a required API key is missing.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is required but not set. Please set this environment variable.")
        
    # Set up Google API configuration
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
    except ImportError:
        raise ValueError("Google Generative AI SDK is not installed. Please install it with: pip install google-generativeai") 