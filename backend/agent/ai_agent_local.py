"""
Local AI Agent implementation (Ollama).

This module provides Ollama-specific LLM initialization and configuration,
using the shared code from agent.py.
"""
import logging

from langchain_ollama import ChatOllama

from agent import (
    app,
    setup_chat_endpoint,
    run_server,
    LOGGER
)
from config import Config


def create_llm():
    """Create and return an Ollama ChatOllama LLM instance."""
    # Validate model is not empty
    model = Config.OLLAMA_MODEL.strip() if Config.OLLAMA_MODEL else None
    if not model or len(model) == 0:
        error_msg = f"OLLAMA_MODEL is not set or is empty. Current value: '{Config.OLLAMA_MODEL}' (type: {type(Config.OLLAMA_MODEL)})"
        LOGGER.error(error_msg)
        raise ValueError(error_msg)
    
    LOGGER.info("create_llm: initializing ChatOllama with model='%s', base_url='%s'", model, Config.OLLAMA_BASE_URL)
    # Ensure model is passed as a non-empty string
    llm = ChatOllama(model=str(model).strip(), base_url=Config.OLLAMA_BASE_URL)
    LOGGER.debug("create_llm: ChatOllama initialized successfully")
    return llm


def get_model_name() -> str:
    """Return the model name for logging."""
    return Config.OLLAMA_MODEL or "ollama"


def get_logger_names() -> list[str]:
    """Return list of logger names to suppress."""
    return ["langchain", "langchain_core", "langchain_community", "langchain_ollama"]


# Setup the chat endpoint with Ollama-specific functions
setup_chat_endpoint(
    create_llm=create_llm
)


def main():
    """Main entry point for Ollama agent."""
    run_server(
        model_name=get_model_name(),
        logger_names=get_logger_names()
    )


if __name__ == "__main__":
    LOGGER.debug("main: entrypoint triggered")
    main()
