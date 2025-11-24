import logging
import os
import re
import requests
from datetime import datetime, UTC
from typing import Dict, Tuple
from dataclasses import dataclass

try:
    from langsmith import uuid7
except ImportError:
    from uuid import uuid4 as uuid7

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, ConfigDict

from prompts import SYSTEM_PROMPT, QUERY_PROMPT, ANALYSIS_PROMPT
from config import Config

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
if Config.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
if Config.LANGCHAIN_PROJECT:
    os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT
if Config.LANGCHAIN_ENDPOINT:
    os.environ["LANGCHAIN_ENDPOINT"] = Config.LANGCHAIN_ENDPOINT
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
# Utility: fetch agent profile from profile service
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
# Utility: mask sensitive data
# ----------------------------------------------------------
def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in text:
    - Mobile numbers: mask the middle 4 digits
    - Email addresses: mask 3-4 letters in the local part (before @)
    """
    masked_text = text
    
    # Mask mobile numbers - find sequences of digits that look like phone numbers (8-15 digits)
    # Match phone numbers in various formats: +61 412 345 678, 0412 345 678, (04) 1234 5678, etc.
    phone_pattern = r'(?:\+?\d{1,3}[-.\s()]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    
    def mask_phone(match):
        phone = match.group(0)
        # Extract only digits
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) >= 8:  # Only mask if it looks like a phone number
            # Mask middle 4 digits
            if len(digits) <= 10:
                # For 8-10 digit numbers: keep first 2 and last 2, mask middle 4
                masked_digits = digits[:2] + '****' + digits[-2:]
            else:
                # For longer numbers: keep first 3 and last 3, mask middle 4
                masked_digits = digits[:3] + '****' + digits[-3:]
            
            # Build masked phone by replacing digits sequentially
            result = list(phone)
            digit_pos = 0
            for i, char in enumerate(result):
                if char.isdigit():
                    if digit_pos < len(masked_digits):
                        result[i] = masked_digits[digit_pos]
                        digit_pos += 1
            return ''.join(result)
        
        return phone
    
    masked_text = re.sub(phone_pattern, mask_phone, masked_text)
    
    # Mask email addresses - mask 3-4 characters in the local part (before @)
    email_pattern = r'\b([a-zA-Z0-9._+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    
    def mask_email(match):
        local_part = match.group(1)
        domain = match.group(2)
        
        # Split local part by dots to handle cases like "john.doe"
        parts = local_part.split('.')
        masked_parts = []
        
        for part in parts:
            # Count only letters in this part
            letters_only = re.sub(r'[^a-zA-Z]', '', part)
            
            if len(letters_only) <= 2:
                # Too short to mask meaningfully
                masked_parts.append(part)
            elif len(letters_only) <= 5:
                # Mask 3 letters, keep first and last letter visible
                first_letter_idx = next((i for i, c in enumerate(part) if c.isalpha()), None)
                last_letter_idx = next((i for i in range(len(part)-1, -1, -1) if part[i].isalpha()), None)
                if first_letter_idx is not None and last_letter_idx is not None:
                    masked_part = part[:first_letter_idx+1] + '***' + part[last_letter_idx:]
                    masked_parts.append(masked_part)
                else:
                    masked_parts.append(part)
            else:
                # Mask 4 letters, keep first and last letter visible
                first_letter_idx = next((i for i, c in enumerate(part) if c.isalpha()), None)
                last_letter_idx = next((i for i in range(len(part)-1, -1, -1) if part[i].isalpha()), None)
                if first_letter_idx is not None and last_letter_idx is not None:
                    masked_part = part[:first_letter_idx+1] + '****' + part[last_letter_idx:]
                    masked_parts.append(masked_part)
                else:
                    masked_parts.append(part)
        
        masked_local = '.'.join(masked_parts)
        return f"{masked_local}@{domain}"
    
    masked_text = re.sub(email_pattern, mask_email, masked_text)
    
    return masked_text


# ----------------------------------------------------------
# Utility: fetch homeowner data from your backend
# ----------------------------------------------------------
def fetch_people(query: str) -> str:
    """Fetch live homeowner data from your local endpoint."""
    LOGGER.debug(">>>>>>>>>>>> fetch_people: starting request for query='%s'", query)
    try:
        response = requests.get(Config.FETCH_URL, params={"q": query})
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
    
    LOGGER.info("create_agent: initializing ChatOpenAI with model='%s', temperature=%s, max_tokens=%s", 
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
    
    llm = ChatOpenAI(**llm_kwargs)
    LOGGER.debug("create_agent: ChatOpenAI initialized successfully")

    # Combine all three prompt components into one template
    # Note: Using string concatenation (not f-strings) to preserve template variables
    combined_prompt = (
        SYSTEM_PROMPT + "\n\n" +
        QUERY_PROMPT + "\n\n" +
        ANALYSIS_PROMPT + "\n\n" +
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
                # OpenAI provides token usage in response_metadata['token_usage']
                if 'token_usage' in metadata:
                    token_usage = metadata['token_usage']
                    input_tokens = token_usage.get('prompt_tokens', token_usage.get('input_tokens', 0))
                    output_tokens = token_usage.get('completion_tokens', token_usage.get('output_tokens', 0))
        
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

    LOGGER.info("process_chat_message: inputs=%s", inputs['question'])
    # Track cumulative token counts for this request
    request_input_tokens = 0
    request_output_tokens = 0

    # First invoke with LangSmith trace context
    response_obj = runnable.invoke(
        inputs,
        config={
            "configurable": {"session_id": session_id},
            "tags": ["chat-agent", f"agent-{profile.agent_id}", "first-invoke"],
            "metadata": {
                "agent_id": profile.agent_id,
                "agent_name": profile.agent_name,
                "location": profile.location,
            },
            "run_name": f"chat-{session_id}-initial",
        },
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
        
        # Mask sensitive data (mobile numbers and emails) before using in follow-up
        masked_data = mask_sensitive_data(data)

        follow_up = (
            f"Here are the search results for '{query}': {masked_data}\n"
            "Please summarise the key opportunities for the agent."
        )

        # Second invoke with LangSmith trace context
        response_obj2 = runnable.invoke(
            {
                "agent_name": profile.agent_name,
                "location": profile.location,
                "listings": ", ".join(profile.listings) if profile.listings else "",
                "question": follow_up,
            },
            config={
                "configurable": {"session_id": session_id},
                "tags": ["chat-agent", f"agent-{profile.agent_id}", "second-invoke", "fetch-followup"],
                "metadata": {
                    "agent_id": profile.agent_id,
                    "agent_name": profile.agent_name,
                    "location": profile.location,
                    "query": query,
                },
                "run_name": f"chat-{session_id}-followup",
            },
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
    allow_origins=Config.CORS_ORIGINS,
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
    logging.getLogger("langchain_openai").setLevel(logging.ERROR)
    
    import uvicorn
    LOGGER.info("Starting AI Agent (model: %s) API server on %s:%d", Config.OPENAI_MODEL, Config.SERVER_HOST, Config.SERVER_PORT)
    uvicorn.run(app, host=Config.SERVER_HOST, port=Config.SERVER_PORT)


if __name__ == "__main__":
    LOGGER.debug("main: entrypoint triggered")
    main()
