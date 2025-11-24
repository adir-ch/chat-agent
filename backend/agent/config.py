"""
Configuration module for the AI Agent service.

All configuration values can be overridden via environment variables.
"""

import os
from typing import List


class Config:
    """Configuration class for the AI Agent service."""
    
    # Ollama configuration
    _ollama_model = os.getenv("OLLAMA_MODEL", "llama3:latest")
    OLLAMA_MODEL = _ollama_model.strip() if _ollama_model else "llama3:latest"
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # LangSmith configuration
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "chat-agent")
    LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "")
    
    # External Model Configuration (OpenAI)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    _openai_temperature = os.getenv("OPENAI_TEMPERATURE", "0.7")
    OPENAI_TEMPERATURE = float(_openai_temperature) if _openai_temperature else 0.7
    _openai_max_tokens = os.getenv("OPENAI_MAX_TOKENS", "")
    OPENAI_MAX_TOKENS = int(_openai_max_tokens) if _openai_max_tokens else None
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    
    # Service URLs
    FETCH_URL = os.getenv("FETCH_URL", "http://localhost:8090/search/smart")
    PROFILE_URL = os.getenv("PROFILE_URL", "http://localhost:8080")
    
    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8070"))
    
    # CORS configuration
    _cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()]

