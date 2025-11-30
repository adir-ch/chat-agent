"""
External AI Agent implementation (OpenAI/GPT).

This module provides OpenAI/GPT-specific LLM initialization, embedding support,
and configuration, using the shared code from agent.py.
"""
import json
import logging

from langchain_openai import ChatOpenAI

from agent import (
    app,
    setup_chat_endpoint,
    setup_streaming_endpoint,
    run_server
)
from utils import mask_sensitive_data, LOGGER
from config import Config

# Conditionally import EmbeddingService only if embeddings are enabled
EmbeddingService = None
if Config.USE_EMBEDDINGS:
    try:
        from embeddings import EmbeddingService
    except ImportError as e:
        logging.warning(f"Failed to import EmbeddingService: {e}. Embeddings will be disabled.")
        Config.USE_EMBEDDINGS = False


def create_llm():
    """Create and return an OpenAI ChatOpenAI LLM instance."""
    # Validate OpenAI API key is set
    api_key = Config.OPENAI_API_KEY.strip() if Config.OPENAI_API_KEY else None
    if not api_key or len(api_key) == 0:
        error_msg = f"OPENAI_API_KEY is not set or is empty. Please set the OPENAI_API_KEY environment variable."
        LOGGER.error(error_msg)
        raise ValueError(error_msg)
    
    # Get model and parameters
    model = Config.OPENAI_MODEL.strip() if Config.OPENAI_MODEL else "gpt-4o-mini"
    temperature = Config.OPENAI_TEMPERATURE
    max_tokens = Config.OPENAI_MAX_TOKENS
    base_url = Config.OPENAI_BASE_URL.strip() if Config.OPENAI_BASE_URL else None
    
    LOGGER.info("create_llm: initializing ChatOpenAI with model='%s', temperature=%s, max_tokens=%s", 
                model, temperature, max_tokens)
    
    # Initialize OpenAI chat model
    llm_kwargs = {
        "model": model,
        "api_key": api_key,
        "temperature": temperature,
    }
    if max_tokens:
        llm_kwargs["max_tokens"] = max_tokens
    if base_url:
        llm_kwargs["base_url"] = base_url
    
    # Always enable streaming capability - invoke() will still wait for complete response
    # but astream() will stream tokens when used for streaming endpoints
    llm_kwargs["streaming"] = True
    llm = ChatOpenAI(**llm_kwargs)
    LOGGER.debug("create_llm: ChatOpenAI initialized with streaming capability")
    return llm


def get_model_name() -> str:
    """Return the model name for logging."""
    return Config.OPENAI_MODEL or "gpt"


def get_logger_names() -> list[str]:
    """Return list of logger names to suppress."""
    return ["langchain", "langchain_core", "langchain_community", "langchain_openai"]


def process_fetch_data(data: str, query: str) -> str:
    """
    Process fetched data for GPT model.
    Handles embeddings if enabled, otherwise just masks sensitive data.
    
    Args:
        data: Raw JSON string from fetch_people()
        query: The search query used to fetch the data
    
    Returns:
        Processed and masked data string
    """
    # Parse JSON response
    try:
        data_items = json.loads(data)
        if not isinstance(data_items, list):
            LOGGER.warning(f"Expected list but got {type(data_items)}, wrapping in list")
            data_items = [data_items] if data_items else []
    except json.JSONDecodeError as e:
        LOGGER.error(f"Failed to parse JSON from fetch_people: {e}")
        LOGGER.debug(f"Response data: {data[:200]}...")  # Log first 200 chars
        data_items = []
    except Exception as e:
        LOGGER.error(f"Unexpected error parsing JSON: {e}")
        data_items = []
    
    # Handle empty results
    if not data_items:
        return "No results found for your query."
    
    # Use embeddings if enabled, otherwise use all data
    if Config.USE_EMBEDDINGS and EmbeddingService is not None:
        # Generate embeddings and find most relevant records
        relevant_items = []
        try:
            # Initialize embedding service
            embedding_service = EmbeddingService()
            
            # Prepare texts for embedding
            texts = [embedding_service.prepare_text_for_embedding(item) for item in data_items]
            
            # Generate embeddings for all records
            LOGGER.info(f"Generating embeddings for {len(data_items)} records...")
            embeddings = embedding_service.generate_embeddings(texts)
            
            # Search for most relevant records
            LOGGER.info(f"Searching for top {Config.EMBEDDING_TOP_K} relevant records...")
            relevant_items = embedding_service.search_similar(
                query=query,
                data_items=data_items,
                embeddings=embeddings,
                top_k=Config.EMBEDDING_TOP_K
            )
            
            LOGGER.info(f"Retrieved {len(relevant_items)} relevant records out of {len(data_items)} total")
            
        except Exception as e:
            LOGGER.error(f"Error generating embeddings or searching: {e}", exc_info=True)
            # Fallback: use first N records
            fallback_count = min(Config.EMBEDDING_TOP_K, len(data_items))
            relevant_items = data_items[:fallback_count]
            LOGGER.warning(f"Falling back to first {fallback_count} records due to embedding error")
        
        # Format relevant records as JSON
        formatted_data = json.dumps(relevant_items, indent=2)
        
        # Mask sensitive data (mobile numbers and emails) before using in follow-up
        masked_data = mask_sensitive_data(formatted_data)
        
        return masked_data
    else:
        # Embeddings disabled - use all data as before
        # Mask sensitive data (mobile numbers and emails) before using in follow-up
        masked_data = mask_sensitive_data(data)
        return masked_data


# Setup the chat endpoint with GPT-specific functions
setup_chat_endpoint(
    create_llm=create_llm,
    process_fetch_data=process_fetch_data
)

# Setup the streaming chat endpoint with GPT-specific functions
setup_streaming_endpoint(
    create_llm=create_llm,
    process_fetch_data=process_fetch_data
)


def main():
    """Main entry point for GPT agent."""
    run_server(
        model_name=get_model_name(),
        logger_names=get_logger_names()
    )


if __name__ == "__main__":
    LOGGER.debug("main: entrypoint triggered")
    main()
