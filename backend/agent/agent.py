"""
Shared AI Agent implementation.

This module contains all common code for the AI agent that works with any LLM model.
Model-specific implementations (ai_agent_local.py, ai_agent_gpt.py) import from this
module and provide model-specific LLM creation and configuration.
"""
import json
import logging
import os
import requests
import time
from datetime import datetime, UTC
from typing import Callable, Optional, Tuple

try:
    from langsmith import uuid7
except ImportError:
    from uuid import uuid4 as uuid7

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, ConfigDict

from config import Config
from prompts import get_llm_prompt, format_follow_up
from models import AgentProfile, TokenUsage
from utils import fetch_people, mask_sensitive_data, track_and_log_token_usage, LOGGER
from sessions import agent_sessions

# Configure LangSmith tracing (common for all models)
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
if Config.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
if Config.LANGCHAIN_PROJECT:
    os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT
if Config.LANGCHAIN_ENDPOINT:
    os.environ["LANGCHAIN_ENDPOINT"] = Config.LANGCHAIN_ENDPOINT


# ----------------------------------------------------------
# Pydantic models for API
# ----------------------------------------------------------
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields
    
    agentId: str
    message: str


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    createdAt: str


class TokenUsageResponse(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    message: ChatMessage
    contextSummary: str | None = None
    tokenUsage: TokenUsageResponse | None = None


# ----------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------
def fetch_agent_profile(agent_id: str) -> AgentProfile:
    """Fetch agent profile from the profile service."""
    LOGGER.info("fetch_agent_profile: fetching profile for agent_id='%s'", agent_id)
    try:
        url = f"{Config.PROFILE_URL}/api/profile/{agent_id}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        profile_data = response.json()
        
        # Map profile data to AgentProfile
        # agent_name: first_name + last_name or fallback to agent_id
        first_name = profile_data.get("first_name", "")
        last_name = profile_data.get("last_name", "")
        if first_name or last_name:
            agent_name = f"{first_name} {last_name}".strip()
        else:
            agent_name = profile_data.get("agent_id", agent_id)
        
        # location: first area name or empty string
        areas = profile_data.get("areas", [])
        location = areas[0].get("name", "") if areas else ""
        
        # listings: format as ["address, suburb"]
        listings_data = profile_data.get("listings", [])
        listings = []
        for listing in listings_data:
            address = listing.get("address", "")
            suburb = listing.get("suburb", "")
            if address and suburb:
                listings.append(f"{address}, {suburb}")
            elif address:
                listings.append(address)
        
        profile = AgentProfile(
            agent_id=agent_id,
            agent_name=agent_name,
            location=location,
            listings=listings
        )
        
        LOGGER.info("fetch_agent_profile: successfully fetched profile - name='%s', location='%s', listings=%d", 
                   agent_name, location, len(listings))
        return profile
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            LOGGER.warning("fetch_agent_profile: profile not found for agent_id='%s'", agent_id)
            raise ValueError(f"Profile not found for agent {agent_id}")
        else:
            LOGGER.error("fetch_agent_profile: HTTP error fetching profile: %s", e)
            raise
    except requests.exceptions.RequestException as e:
        LOGGER.error("fetch_agent_profile: network error fetching profile: %s", e)
        raise
    except Exception as e:
        LOGGER.error("fetch_agent_profile: unexpected error fetching profile: %s", e)
        raise




# ----------------------------------------------------------
# Agent Creation (Model-Agnostic)
# ----------------------------------------------------------
def create_agent(
    agent_name: str,
    location: str,
    listings: list[str],
    create_llm: Callable
) -> Tuple[RunnableWithMessageHistory, ChatMessageHistory]:
    """
    Create an agent chain with the provided LLM creation function.
    
    Args:
        agent_name: Name of the agent
        location: Location of the agent
        listings: List of property listings
        create_llm: Function that creates and returns an LLM instance
    
    Returns:
        Tuple of (runnable, history)
    """
    LOGGER.debug("create_agent: initializing agent='%s' location='%s' listings=%s",
                 agent_name, location, listings)

    # Create LLM using model-specific function
    llm = create_llm()
    LOGGER.debug("create_agent: LLM initialized successfully")

    # Get prompt template using get_llm_prompt from prompts module
    prompt_template_str = get_llm_prompt()
    
    # Combine prompt template with conversation context
    combined_prompt = (
        prompt_template_str + "\n\n" +
        "Conversation so far:\n{chat_history}\n\n" +
        "User question: {question}"
    )
    
    prompt = ChatPromptTemplate.from_template(combined_prompt)
    LOGGER.debug("create_agent: ChatPromptTemplate ready")

    # Use modern message-based memory
    history = ChatMessageHistory()

    chain = prompt | llm

    # Wrap with message-history memory
    runnable = RunnableWithMessageHistory(
        chain,
        lambda session_id: history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    LOGGER.debug("create_agent: chain assembled")
    return runnable, history


# Import chat module after create_agent is defined to avoid circular dependency
from chat import process_chat_message, process_chat_message_stream


# ----------------------------------------------------------
# FastAPI app setup
# ----------------------------------------------------------
app = FastAPI(title="AI Agent API", version="1.0.0")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


def setup_chat_endpoint(
    create_llm: Callable,
    process_fetch_data: Optional[Callable[[str, str], str]] = None
):
    """
    Setup the /chat endpoint with model-specific functions.
    
    Args:
        create_llm: Function that creates and returns an LLM instance
        process_fetch_data: Optional function to process fetched data
    """
    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest):
        """
        Chat endpoint that processes messages through the AI agent.
        """
        try:
            # Use agentId as session_id for conversation history
            session_id = request.agentId
            
            LOGGER.info("chat_endpoint: processing message for agentId='%s', session_id='%s'", request.agentId, session_id)
            
            # Fetch or get cached profile for this session
            profile = None
            if session_id in agent_sessions:
                # Profile already cached in session
                _, _, profile, _ = agent_sessions[session_id]
                LOGGER.debug("chat_endpoint: using cached profile for session_id='%s'", session_id)
            else:
                # Fetch profile from profile service
                try:
                    profile = fetch_agent_profile(request.agentId)
                except ValueError as e:
                    # Profile not found (404) - use fallback
                    LOGGER.warning("chat_endpoint: profile not found, using fallback: %s", e)
                    profile = AgentProfile(
                        agent_id=request.agentId,
                        agent_name=request.agentId,
                        location="",
                        listings=[]
                    )
                except Exception as e:
                    # Network or other error - use fallback
                    LOGGER.error("chat_endpoint: error fetching profile, using fallback: %s", e)
                    profile = AgentProfile(
                        agent_id=request.agentId,
                        agent_name=request.agentId,
                        location="",
                        listings=[]
                    )
            
            # Process the chat message
            response_content, input_tokens, output_tokens = process_chat_message(
                profile=profile,
                question=request.message,
                session_id=session_id,
                create_llm=create_llm,
                process_fetch_data=process_fetch_data
            )
            
            # Create response message
            message = ChatMessage(
                id=str(uuid7()),
                role="assistant",
                content=response_content,
                createdAt=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
            )
            
            # Create token usage response
            token_usage = TokenUsageResponse(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens
            )
            
            return ChatResponse(message=message, tokenUsage=token_usage)
            
        except Exception as e:
            LOGGER.error("chat_endpoint: error processing request: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    return chat_endpoint


def setup_streaming_endpoint(
    create_llm: Callable,
    process_fetch_data: Optional[Callable[[str, str], str]] = None
):
    """
    Setup the /chat/stream endpoint with model-specific functions for streaming.
    
    Args:
        create_llm: Function that creates and returns an LLM instance
        process_fetch_data: Optional function to process fetched data
    """
    @app.post("/chat/stream")
    async def chat_stream_endpoint(request: ChatRequest):
        """
        Streaming chat endpoint that processes messages through the AI agent and streams tokens.
        Returns Server-Sent Events (SSE) format.
        """
        async def generate_stream():
            try:
                # Use agentId as session_id for conversation history
                session_id = request.agentId
                
                # Check if streaming is enabled in config
                if not Config.ENABLE_STREAMING:
                    error_data = {"error": "Streaming is disabled in configuration"}
                    yield f"data: {json.dumps(error_data)}\n\n"
                    return
                
                LOGGER.info("chat_stream_endpoint: processing streaming message for agentId='%s', session_id='%s'", request.agentId, session_id)
                
                # Fetch or get cached profile for this session
                profile = None
                if session_id in agent_sessions:
                    # Profile already cached in session
                    _, _, profile, _ = agent_sessions[session_id]
                    LOGGER.debug("chat_stream_endpoint: using cached profile for session_id='%s'", session_id)
                else:
                    # Fetch profile from profile service
                    try:
                        profile = fetch_agent_profile(request.agentId)
                    except ValueError as e:
                        # Profile not found (404) - use fallback
                        LOGGER.warning("chat_stream_endpoint: profile not found, using fallback: %s", e)
                        profile = AgentProfile(
                            agent_id=request.agentId,
                            agent_name=request.agentId,
                            location="",
                            listings=[]
                        )
                    except Exception as e:
                        # Network or other error - use fallback
                        LOGGER.error("chat_stream_endpoint: error fetching profile, using fallback: %s", e)
                        profile = AgentProfile(
                            agent_id=request.agentId,
                            agent_name=request.agentId,
                            location="",
                            listings=[]
                        )
                
                # Create message ID for this response
                message_id = str(uuid7())
                message_created_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                
                # Process the chat message with streaming
                final_input_tokens = 0
                final_output_tokens = 0
                
                async for token_chunk, input_tokens, output_tokens in process_chat_message_stream(
                    profile=profile,
                    question=request.message,
                    session_id=session_id,
                    create_llm=create_llm,
                    process_fetch_data=process_fetch_data
                ):
                    # Update final token counts (last chunk will have the totals)
                    if input_tokens > 0 or output_tokens > 0:
                        final_input_tokens = input_tokens
                        final_output_tokens = output_tokens
                    
                    # Send token chunk as SSE
                    if token_chunk:
                        # Escape newlines for SSE format
                        escaped_chunk = token_chunk.replace('\n', '\\n').replace('\r', '\\r')
                        yield f"data: {escaped_chunk}\n\n"
                
                # Send final message with token usage
                final_data = {
                    "messageId": message_id,
                    "createdAt": message_created_at,
                    "tokenUsage": {
                        "input_tokens": final_input_tokens,
                        "output_tokens": final_output_tokens,
                        "total_tokens": final_input_tokens + final_output_tokens
                    }
                }
                yield f"data: {json.dumps(final_data)}\n\n"
                
            except Exception as e:
                LOGGER.error("chat_stream_endpoint: error processing request: %s", e, exc_info=True)
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering for nginx
            }
        )
    
    return chat_stream_endpoint


def run_server(model_name: str, logger_names: list[str]):
    """
    Run the FastAPI server with model-specific configuration.
    
    Args:
        model_name: Name of the model for logging
        logger_names: List of logger names to suppress
    """
    LOGGER.debug("run_server: starting application setup")
    
    # Suppress LangChain log output
    for logger_name in logger_names:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    import uvicorn
    LOGGER.info("Starting AI Agent (model: %s) API server on %s:%d", model_name, Config.SERVER_HOST, Config.SERVER_PORT)
    uvicorn.run(app, host=Config.SERVER_HOST, port=Config.SERVER_PORT)

