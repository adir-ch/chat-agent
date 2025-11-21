import logging
import os
import requests
from datetime import datetime, UTC
from typing import Dict, Tuple
from dataclasses import dataclass

# Disable LangSmith tracing to avoid UUID v7 warnings
os.environ["LANGCHAIN_TRACING_V2"] = "false"

try:
    from langsmith import uuid7
except ImportError:
    from uuid import uuid4 as uuid7

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel

MODEL = "llama3:latest" #"qwen3:0.6b" #"gemma3:1b" #
FETCH_URL = "http://localhost:8090/search/smart"
PROFILE_URL = os.getenv("PROFILE_URL", "http://localhost:8080")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# # Silence noisy HTTP logs
# for name in ["httpx", "httpcore", "urllib3"]:
#     logging.getLogger(name).setLevel(logging.WARNING)

# # Optionally silence LangChain internals too
# for name in ["langchain", "langchain_core", "langchain_community", "langchain_ollama"]:
#     logging.getLogger(name).setLevel(logging.ERROR)

LOGGER = logging.getLogger(__name__)

# Profile data structure
class AgentProfile:
    def __init__(self, agent_id: str, agent_name: str, location: str, listings: list[str]):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.location = location
        self.listings = listings


# Token usage tracking
@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def add(self, input_tokens: int, output_tokens: int):
        """Add tokens to the cumulative totals."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
    
    def reset(self):
        """Reset token counts to zero."""
        self.input_tokens = 0
        self.output_tokens = 0


# Session management: maps agentId -> (runnable, history, profile, token_usage)
agent_sessions: Dict[str, Tuple[RunnableWithMessageHistory, ChatMessageHistory, AgentProfile, TokenUsage]] = {}


# ----------------------------------------------------------
# Pydantic models for API
# ----------------------------------------------------------
class ChatRequest(BaseModel):
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
# Utility: fetch agent profile from profile service
# ----------------------------------------------------------
def fetch_agent_profile(agent_id: str) -> AgentProfile:
    """Fetch agent profile from the profile service."""
    LOGGER.info("fetch_agent_profile: fetching profile for agent_id='%s'", agent_id)
    try:
        url = f"{PROFILE_URL}/api/profile/{agent_id}"
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
# Utility: fetch homeowner data from your backend
# ----------------------------------------------------------
def fetch_people(query: str) -> str:
    """Fetch live homeowner data from your local endpoint."""
    LOGGER.debug(">>>>>>>>>>>> fetch_people: starting request for query='%s'", query)
    try:
        response = requests.get(FETCH_URL, params={"q": query})
        response.raise_for_status()
        #LOGGER.debug("fetch_people: completed request with status=%s", response.status_code)
        LOGGER.debug(">>>>>>>>>>>> fetch_people: completed request with: %s", response.text)
        return response.text
    except Exception as e:
        LOGGER.debug("fetch_people: request failed with error=%s", e)
        return f"Error fetching data: {e}"


# ----------------------------------------------------------
# Agent creation
# ----------------------------------------------------------
def create_agent(agent_name: str, location: str, listings: list[str]):
    LOGGER.debug("create_agent: initializing agent='%s' location='%s' listings=%s",
                 agent_name, location, listings)

    llm = ChatOllama(model=MODEL, base_url="http://localhost:11434")
    LOGGER.debug("create_agent: ChatOllama initialized with model=%s", MODEL)

    # prompt = ChatPromptTemplate.from_template(
    #     "You are a helpful real estate assistant working with agent {agent_name} in {location}. "
    #     "Their current listings are: {listings}. "
    #     "If you need live homeowner or prospect data, respond ONLY with:\n"
    #     "FETCH: <search terms to send to the data service>\n\n"
    #     "Conversation so far:\n{chat_history}\n\n"
    #     "User question: {question}"
    # )

    # prompt = ChatPromptTemplate.from_template(
    #     "You are a helpful real estate assistant working with agent {agent_name} in {location}. "
    #     "Their current listings are: {listings}. "
    #     "\n\n"
    #     "If you need live homeowner or prospect data, you must respond ONLY in the following format:\n"
    #     "FETCH: <suburb name or postcode>\n\n"
    #     "Rules for FETCH:\n"
    #     "- Never include full street addresses.\n"
    #     "- Never include commas, unit numbers, or street names.\n"
    #     "- Always use just a suburb or postcode.\n"
    #     "- Do not include any explanations, punctuation, or text other than the FETCH line.\n\n"
    #     "Conversation so far:\n{chat_history}\n\n"
    #     "User question: {question}"
    # )

    prompt = ChatPromptTemplate.from_template(
        "You are a helpful real estate assistant working with agent {agent_name} in {location}. "
        "Their current listings are: {listings}.\n\n"
        "You operate in two modes:\n"
        "1. Query Mode – When you do NOT yet have homeowner or prospect data:\n"
        "   • Respond ONLY in the format:  FETCH: <users query>\n"
        "   • Follow these rules:\n"
        "     - Never include full street addresses or commas.\n"
        "     - Use only a suburb or postcode.\n"
        "     - Output nothing except the single FETCH line.\n\n"
        "2. Analysis Mode – When the user provides homeowner or prospect data "
        "(you will see text like 'Here are the search results...' or 'Data:' in the conversation):\n"
        "   • Do NOT use FETCH again.\n"
        "   • Analyse the provided data and summarise key opportunities for the agent, "
        "     such as potential leads, timing, or market insights.\n\n"
        "Conversation so far:\n{chat_history}\n\n"
        "User question: {question}"
        "Provide the answers in a Markdown format"
    )


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


# ----------------------------------------------------------
# Chat processing logic
# ----------------------------------------------------------
def extract_token_usage(response) -> Tuple[int, int]:
    """
    Extract token usage from LLM response metadata.
    Returns (input_tokens, output_tokens) tuple.
    """
    input_tokens = 0
    output_tokens = 0
    
    try:
        # LangChain AIMessage objects have response_metadata
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            if metadata:
                # Ollama typically provides token usage in different formats
                # Try common field names
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    input_tokens = token_usage.get('prompt_tokens', token_usage.get('input_tokens', 0))
                    output_tokens = token_usage.get('completion_tokens', token_usage.get('output_tokens', 0))
                elif 'prompt_tokens' in metadata:
                    input_tokens = metadata.get('prompt_tokens', 0)
                    output_tokens = metadata.get('completion_tokens', metadata.get('eval_count', 0))
                elif 'eval_count' in metadata:
                    # Ollama format: eval_count is output tokens, prompt_eval_count is input tokens
                    output_tokens = metadata.get('eval_count', 0)
                    input_tokens = metadata.get('prompt_eval_count', 0)
        
        # Also check if response has usage_metadata attribute (some LangChain versions)
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            if usage:
                input_tokens = getattr(usage, 'input_tokens', input_tokens)
                output_tokens = getattr(usage, 'output_tokens', output_tokens)
        
        # Debug: log the response structure if no tokens found
        if input_tokens == 0 and output_tokens == 0:
            LOGGER.debug("extract_token_usage: no tokens found in response. Available attributes: %s", 
                        dir(response) if hasattr(response, '__dict__') else 'N/A')
    except Exception as e:
        LOGGER.debug("extract_token_usage: error extracting tokens: %s", e)
    
    return input_tokens, output_tokens


def track_and_log_token_usage(response, token_usage: TokenUsage, session_id: str, invoke_label: str = "invoke") -> Tuple[int, int]:
    """
    Extract token usage from LLM response, update session totals, and log the information.
    
    Args:
        response: The LLM response object
        token_usage: The TokenUsage object for the session
        session_id: The session identifier for logging
        invoke_label: Label to identify which invoke this is (e.g., "first invoke", "second invoke")
    
    Returns:
        Tuple[int, int]: (input_tokens, output_tokens) for this invocation
    """
    # Extract token usage from response
    input_tokens, output_tokens = extract_token_usage(response)
    
    # Update session token totals
    token_usage.add(input_tokens, output_tokens)
    
    # Log token usage information
    LOGGER.info(
        "Token usage for session '%s' (%s): Input: %d, Output: %d, Total: %d | "
        "Session totals: Input: %d, Output: %d, Total: %d",
        session_id,
        invoke_label,
        input_tokens, output_tokens, input_tokens + output_tokens,
        token_usage.input_tokens, token_usage.output_tokens, token_usage.total_tokens
    )
    
    return input_tokens, output_tokens


def process_chat_message(profile: AgentProfile, question: str, session_id: str) -> Tuple[str, int, int]:
    """
    Process a chat message through the agent chain.
    Handles FETCH: responses by calling fetch_people() and making follow-up invoke.
    
    Returns:
        Tuple[str, int, int]: (response_text, total_input_tokens, total_output_tokens)
        Token counts are cumulative for all invocations in this request.
    """
    # Get or create agent chain/history for this session
    if session_id not in agent_sessions:
        LOGGER.debug("process_chat_message: creating new agent for session_id='%s'", session_id)
        runnable, history = create_agent(profile.agent_name, profile.location, profile.listings)
        token_usage = TokenUsage()
        agent_sessions[session_id] = (runnable, history, profile, token_usage)
    else:
        LOGGER.debug("process_chat_message: reusing existing agent for session_id='%s'", session_id)
        runnable, history, _, token_usage = agent_sessions[session_id]
        # Update profile in case it changed
        agent_sessions[session_id] = (runnable, history, profile, token_usage)

    inputs = {
        "agent_name": profile.agent_name,
        "location": profile.location,
        "listings": ", ".join(profile.listings) if profile.listings else "",
        "question": question,
    }

    # Track cumulative token counts for this request
    request_input_tokens = 0
    request_output_tokens = 0

    # First invoke
    response_obj = runnable.invoke(
        inputs,
        config={"configurable": {"session_id": session_id}},
    )
    response = response_obj.content.strip()
    
    # Track and log token usage, accumulate for this request
    input_tokens1, output_tokens1 = track_and_log_token_usage(response_obj, token_usage, session_id, "first invoke")
    request_input_tokens += input_tokens1
    request_output_tokens += output_tokens1

    if response.upper().startswith("FETCH:"):
        LOGGER.info(">>>>>>>> first invoke: %s", response)

        query = response[6:].strip()
        LOGGER.info("🔍 Fetching data for: %s", query)
        data = fetch_people(query)

        follow_up = (
            f"Here are the search results for '{query}': {data}\n"
            "Please summarise the key opportunities for the agent."
        )

        # Second invoke
        response_obj2 = runnable.invoke(
            {
                "agent_name": profile.agent_name,
                "location": profile.location,
                "listings": ", ".join(profile.listings) if profile.listings else "",
                "question": follow_up,
            },
            config={"configurable": {"session_id": session_id}},
        )
        response = response_obj2.content.strip()
        
        # Track and log token usage, accumulate for this request
        input_tokens2, output_tokens2 = track_and_log_token_usage(response_obj2, token_usage, session_id, "second invoke")
        request_input_tokens += input_tokens2
        request_output_tokens += output_tokens2
        LOGGER.info(">>>>>>>>>>> second invoke: %s:\n%s", follow_up, response)

    return response, request_input_tokens, request_output_tokens


# ----------------------------------------------------------
# FastAPI app setup
# ----------------------------------------------------------
app = FastAPI(title="AI Agent API", version="1.0.0")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


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
            session_id=session_id
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


# ----------------------------------------------------------
# Main application entry point
# ----------------------------------------------------------
def main():
    LOGGER.debug("main: starting application setup")
    
    # Suppress LangChain log output
    logging.getLogger("langchain").setLevel(logging.ERROR)
    logging.getLogger("langchain_core").setLevel(logging.ERROR)
    logging.getLogger("langchain_community").setLevel(logging.ERROR)
    logging.getLogger("langchain_ollama").setLevel(logging.ERROR)
    
    import uvicorn
    LOGGER.info("Starting AI Agent API server on port 8070")
    uvicorn.run(app, host="0.0.0.0", port=8070)


if __name__ == "__main__":
    LOGGER.debug("main: entrypoint triggered")
    main()
