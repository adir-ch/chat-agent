"""
Configuration module for the AI Agent service.

Configuration values are loaded from config.json first, then environment variables,
then defaults. API keys are only loaded from environment variables.
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Any, Optional


class ConfigError(Exception):
    """Exception raised when configuration is invalid."""
    pass


def _print_documentation():
    """Print the documentation from config.json."""
    config_path = Path(__file__).parent / "config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                doc = config_data.get("_documentation", {})
                if doc:
                    print("\n" + "="*70)
                    print("CONFIGURATION DOCUMENTATION")
                    print("="*70)
                    print(f"\n{doc.get('description', '')}\n")
                    print("Available Configuration Options:")
                    print("-" * 70)
                    for key, value in doc.items():
                        if key != "description":
                            print(f"  {key}: {value}")
                    print("="*70 + "\n")
    except Exception:
        pass


def _get_model_config(models: List[dict], model_type: str) -> Optional[dict]:
    """
    Get model configuration by type from the models array.
    
    Args:
        models: List of model configuration dictionaries
        model_type: Type of model to find (any string)
    
    Returns:
        Model configuration dictionary or None if not found
    """
    if not isinstance(models, list):
        return None
    
    for model in models:
        if isinstance(model, dict) and model.get("type") == model_type:
            return model
    return None


def _validate_config(agent_config: dict):
    """Validate configuration values."""
    errors = []
    
    # Validate models array structure
    # All models must have the same required fields regardless of type
    if "models" in agent_config:
        models = agent_config["models"]
        if not isinstance(models, list):
            errors.append("'models' must be an array")
        elif len(models) == 0:
            errors.append("'models' array must contain at least one model configuration")
        else:
            # Required fields that all models must have
            required_fields = ["type", "model", "temperature", "max_tokens", "base_url"]
            
            for i, model in enumerate(models):
                if not isinstance(model, dict):
                    errors.append(f"models[{i}] must be an object")
                    continue
                
                # Validate required fields for all models
                for field in required_fields:
                    if field not in model:
                        errors.append(f"models[{i}] must have a '{field}' field")
                
                # Validate type field is a string
                model_type = model.get("type")
                if model_type is not None and not isinstance(model_type, str):
                    errors.append(f"models[{i}] 'type' field must be a string")
                
                # Validate temperature if present (must be number between 0 and 2)
                if "temperature" in model:
                    try:
                        temp = model["temperature"]
                        if temp is not None:
                            temp_float = float(temp) if isinstance(temp, str) else temp
                            if not isinstance(temp_float, (int, float)) or temp_float < 0 or temp_float > 2:
                                errors.append(f"models[{i}] temperature must be a number between 0 and 2, got: {temp}")
                    except (ValueError, TypeError):
                        errors.append(f"models[{i}] temperature must be a number, got: {model['temperature']}")
                
                # Validate max_tokens if present (must be integer or null)
                if "max_tokens" in model:
                    max_tokens = model["max_tokens"]
                    if max_tokens is not None:
                        try:
                            max_tokens_int = int(max_tokens) if isinstance(max_tokens, str) else max_tokens
                            if not isinstance(max_tokens_int, int) or max_tokens_int < 1:
                                errors.append(f"models[{i}] max_tokens must be a positive integer or null, got: {max_tokens}")
                        except (ValueError, TypeError):
                            errors.append(f"models[{i}] max_tokens must be an integer or null, got: {max_tokens}")
                
                # Validate base_url if present (must be string)
                if "base_url" in model and model["base_url"] is not None:
                    if not isinstance(model["base_url"], str):
                        errors.append(f"models[{i}] base_url must be a string, got: {type(model['base_url']).__name__}")
    else:
        errors.append("'models' array is required in agent_config")
    
    # Validate server_port is an integer
    if "server_port" in agent_config:
        try:
            port = agent_config["server_port"]
            if port is not None:
                port_int = int(port) if isinstance(port, str) else port
                if not isinstance(port_int, int) or port_int < 1 or port_int > 65535:
                    errors.append(f"server_port must be an integer between 1 and 65535, got: {port}")
        except (ValueError, TypeError):
            errors.append(f"server_port must be an integer, got: {agent_config['server_port']}")
    
    # Validate embedding_top_k is an integer
    if "embedding_top_k" in agent_config:
        try:
            top_k = agent_config["embedding_top_k"]
            if top_k is not None:
                top_k_int = int(top_k) if isinstance(top_k, str) else top_k
                if not isinstance(top_k_int, int) or top_k_int < 1:
                    errors.append(f"embedding_top_k must be a positive integer, got: {top_k}")
        except (ValueError, TypeError):
            errors.append(f"embedding_top_k must be an integer, got: {agent_config['embedding_top_k']}")
    
    # Validate use_embeddings is a boolean
    if "use_embeddings" in agent_config:
        val = agent_config["use_embeddings"]
        if not isinstance(val, bool) and val not in ("true", "false", "True", "False", "1", "0"):
            errors.append(f"use_embeddings must be a boolean (true/false), got: {val}")
    
    # Validate cors_origins is a list
    if "cors_origins" in agent_config:
        val = agent_config["cors_origins"]
        if not isinstance(val, list):
            errors.append(f"cors_origins must be an array, got: {type(val).__name__}")
    
    if errors:
        error_msg = "Configuration validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigError(error_msg)


def _load_json_config() -> dict:
    """Load and validate configuration from config.json file."""
    config_path = Path(__file__).parent / "config.json"
    
    if not config_path.exists():
        raise ConfigError(f"config.json not found at {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config.json: {e}")
    except IOError as e:
        raise ConfigError(f"Error reading config.json: {e}")
    
    agent_config = config_data.get("agent_config")
    if agent_config is None:
        raise ConfigError("config.json must contain an 'agent_config' object")
    
    if not isinstance(agent_config, dict):
        raise ConfigError("'agent_config' must be a JSON object")
    
    # Validate configuration values
    _validate_config(agent_config)
    
    return agent_config


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


def _get_model_config_value(model_config: Optional[dict], key: str, env_key: str, default: Any) -> Any:
    """
    Get model configuration value with priority: Model Config > Environment Variable > Default.
    
    Args:
        model_config: Model configuration dictionary from models array
        key: Key in model config
        env_key: Environment variable name
        default: Default value if not found in model config or env
    
    Returns:
        Configuration value
    """
    # Check model config first
    if model_config and key in model_config and model_config[key] is not None:
        return model_config[key]
    
    # Check environment variable
    env_value = os.getenv(env_key)
    if env_value is not None and env_value != "":
        return env_value
    
    # Use default
    return default


class Config:
    """Configuration class for the AI Agent service."""
    
    # Load JSON config once
    try:
        _json_config = _load_json_config()
    except ConfigError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get model configurations from models array
    _models = _json_config.get("models", [])
    _ollama_config = _get_model_config(_models, "ollama")
    _openai_config = _get_model_config(_models, "openai")
    
    # Ollama configuration
    _ollama_model = _get_model_config_value(_ollama_config, "model", "OLLAMA_MODEL", "llama3:latest")
    OLLAMA_MODEL = _ollama_model.strip() if _ollama_model else "llama3:latest"
    OLLAMA_BASE_URL = _get_model_config_value(_ollama_config, "base_url", "OLLAMA_BASE_URL", "http://localhost:11434")
    _ollama_max_tokens = _get_model_config_value(_ollama_config, "max_tokens", "OLLAMA_MAX_TOKENS", None)
    OLLAMA_MAX_TOKENS = int(_ollama_max_tokens) if _ollama_max_tokens else None
    
    # LangSmith configuration
    LANGCHAIN_TRACING_V2 = _get_config_value("langchain_tracing_v2", _json_config, "LANGCHAIN_TRACING_V2", "true")
    # API keys are only loaded from environment variables
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = _get_config_value("langchain_project", _json_config, "LANGCHAIN_PROJECT", "chat-agent")
    LANGCHAIN_ENDPOINT = _get_config_value("langchain_endpoint", _json_config, "LANGCHAIN_ENDPOINT", "")
    
    # External Model Configuration (OpenAI)
    # API keys are only loaded from environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    _openai_model = _get_model_config_value(_openai_config, "model", "OPENAI_MODEL", "gpt-5-mini")
    OPENAI_MODEL = _openai_model.strip() if _openai_model else "gpt-5-mini"
    _openai_temperature = _get_model_config_value(_openai_config, "temperature", "OPENAI_TEMPERATURE", 0.7)
    OPENAI_TEMPERATURE = float(_openai_temperature) if _openai_temperature else 0.7
    _openai_max_tokens = _get_model_config_value(_openai_config, "max_tokens", "OPENAI_MAX_TOKENS", None)
    OPENAI_MAX_TOKENS = int(_openai_max_tokens) if _openai_max_tokens else None
    _openai_base_url = _get_model_config_value(_openai_config, "base_url", "OPENAI_BASE_URL", "")
    OPENAI_BASE_URL = _openai_base_url.strip() if _openai_base_url else ""
    
    # Embedding configuration (kept at top level)
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
    
    # Streaming configuration
    _enable_streaming = _get_config_value("enable_streaming", _json_config, "ENABLE_STREAMING", False)
    ENABLE_STREAMING = str(_enable_streaming).lower() == "true" if isinstance(_enable_streaming, str) else bool(_enable_streaming)
    
    # CORS configuration
    _cors_origins_value = _get_config_value("cors_origins", _json_config, "CORS_ORIGINS", ["http://localhost:5173", "http://localhost:3000"])
    if isinstance(_cors_origins_value, list):
        CORS_ORIGINS: List[str] = _cors_origins_value
    else:
        # Parse string from environment variable or default
        _cors_origins_str = str(_cors_origins_value) if _cors_origins_value else "http://localhost:5173,http://localhost:3000"
        CORS_ORIGINS: List[str] = [origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()]
    
    @staticmethod
    def get_available_model_types() -> List[str]:
        """
        Get list of available model types from the models array.
        
        Returns:
            List of model type strings (e.g., ['ollama', 'openai'])
        """
        models = Config._json_config.get("models", [])
        if not isinstance(models, list):
            return []
        
        model_types = []
        for model in models:
            if isinstance(model, dict) and "type" in model:
                model_type = model["type"]
                if model_type not in model_types:
                    model_types.append(model_type)
        return model_types
    
    @staticmethod
    def validate_model_type(model_type: str) -> bool:
        """
        Validate that a model type exists in the models array.
        
        Args:
            model_type: Model type to validate (e.g., 'ollama', 'openai')
        
        Returns:
            True if model type exists, False otherwise
        """
        available_types = Config.get_available_model_types()
        return model_type in available_types
    
    @staticmethod
    def get_model_config_by_type(model_type: str) -> Optional[dict]:
        """
        Get model configuration by type.
        
        Args:
            model_type: Model type to get (e.g., 'ollama', 'openai')
        
        Returns:
            Model configuration dictionary or None if not found
        """
        return _get_model_config(Config._models, model_type)

