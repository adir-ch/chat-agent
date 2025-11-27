"""
Configuration module for the AI Agent service.

Configuration values are loaded from config.json first, then environment variables,
then defaults. API keys are only loaded from environment variables.
"""

import os
import json
from pathlib import Path
from typing import List, Any, Optional


def _load_json_config() -> dict:
    """Load configuration from config.json file."""
    config_path = Path(__file__).parent / "config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                return config_data.get("agent_config", {})
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _get_config_value(key: str, json_config: dict, env_key: str, default: Any) -> Any:
    """
    Get configuration value with priority: JSON > Environment Variable > Default.
    
    Args:
        key: Key in JSON config
        json_config: Dictionary loaded from JSON
        env_key: Environment variable name
        default: Default value if not found in JSON or env
    
    Returns:
        Configuration value
    """
    # Check JSON first
    if key in json_config and json_config[key] is not None:
        return json_config[key]
    
    # Check environment variable
    env_value = os.getenv(env_key)
    if env_value is not None and env_value != "":
        return env_value
    
    # Use default
    return default


class Config:
    """Configuration class for the AI Agent service."""
    
    # Load JSON config once
    _json_config = _load_json_config()
    
    # Ollama configuration
    _ollama_model = _get_config_value("ollama_model", _json_config, "OLLAMA_MODEL", "llama3:latest")
    OLLAMA_MODEL = _ollama_model.strip() if _ollama_model else "llama3:latest"
    OLLAMA_BASE_URL = _get_config_value("ollama_base_url", _json_config, "OLLAMA_BASE_URL", "http://localhost:11434")
    
    # LangSmith configuration
    LANGCHAIN_TRACING_V2 = _get_config_value("langchain_tracing_v2", _json_config, "LANGCHAIN_TRACING_V2", "true")
    # API keys are only loaded from environment variables
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = _get_config_value("langchain_project", _json_config, "LANGCHAIN_PROJECT", "chat-agent")
    LANGCHAIN_ENDPOINT = _get_config_value("langchain_endpoint", _json_config, "LANGCHAIN_ENDPOINT", "")
    
    # External Model Configuration (OpenAI)
    # API keys are only loaded from environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = _get_config_value("openai_model", _json_config, "OPENAI_MODEL", "gpt-5-mini")
    _openai_temperature = _get_config_value("openai_temperature", _json_config, "OPENAI_TEMPERATURE", 0.7)
    OPENAI_TEMPERATURE = float(_openai_temperature) if _openai_temperature else 0.7
    _openai_max_tokens = _get_config_value("openai_max_tokens", _json_config, "OPENAI_MAX_TOKENS", None)
    OPENAI_MAX_TOKENS = int(_openai_max_tokens) if _openai_max_tokens else None
    OPENAI_BASE_URL = _get_config_value("openai_base_url", _json_config, "OPENAI_BASE_URL", "")
    
    # Embedding configuration
    _use_embeddings = _get_config_value("use_embeddings", _json_config, "USE_EMBEDDINGS", False)
    USE_EMBEDDINGS = str(_use_embeddings).lower() == "true" if isinstance(_use_embeddings, str) else bool(_use_embeddings)
    EMBEDDING_MODEL = _get_config_value("embedding_model", _json_config, "EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_TOP_K = int(_get_config_value("embedding_top_k", _json_config, "EMBEDDING_TOP_K", 5))
    
    # Service URLs
    FETCH_URL = _get_config_value("fetch_url", _json_config, "FETCH_URL", "http://localhost:8090/search/smart")
    PROFILE_URL = _get_config_value("profile_url", _json_config, "PROFILE_URL", "http://localhost:8080")
    
    # Server configuration
    SERVER_HOST = _get_config_value("server_host", _json_config, "SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(_get_config_value("server_port", _json_config, "SERVER_PORT", 8070))
    
    # CORS configuration
    _cors_origins_value = _get_config_value("cors_origins", _json_config, "CORS_ORIGINS", ["http://localhost:5173", "http://localhost:3000"])
    if isinstance(_cors_origins_value, list):
        CORS_ORIGINS: List[str] = _cors_origins_value
    else:
        # Parse string from environment variable or default
        _cors_origins_str = str(_cors_origins_value) if _cors_origins_value else "http://localhost:5173,http://localhost:3000"
        CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()]

