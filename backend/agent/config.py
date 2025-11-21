"""
Configuration module for the AI Agent service.

All configuration values can be overridden via environment variables.
"""

import os
from typing import List


class Config:
    """Configuration class for the AI Agent service."""
    
    # Ollama configuration
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Service URLs
    FETCH_URL = os.getenv("FETCH_URL", "http://localhost:8090/search/smart")
    PROFILE_URL = os.getenv("PROFILE_URL", "http://localhost:8080")
    
    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8070"))
    
    # CORS configuration
    _cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()]

