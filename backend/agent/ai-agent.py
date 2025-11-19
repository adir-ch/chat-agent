import logging
import os
import requests
from datetime import datetime, UTC
from typing import Dict, Tuple

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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# # Silence noisy HTTP logs
# for name in ["httpx", "httpcore", "urllib3"]:
#     logging.getLogger(name).setLevel(logging.WARNING)

# # Optionally silence LangChain internals too
# for name in ["langchain", "langchain_core", "langchain_community", "langchain_ollama"]:
#     logging.getLogger(name).setLevel(logging.ERROR)

LOGGER = logging.getLogger(__name__)

# Hardcoded agent profile data
AGENT_NAME = "agent-123"
LOCATION = "Bondi"
LISTINGS = ["156 Campbell Pde", "88 Beach Rd"]

# Session management: maps agentId -> (runnable, history)
agent_sessions: Dict[str, Tuple[RunnableWithMessageHistory, ChatMessageHistory]] = {}


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


class ChatResponse(BaseModel):
    message: ChatMessage
    contextSummary: str | None = None


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
def process_chat_message(agent_name: str, location: str, listings: list[str], question: str, session_id: str) -> str:
    """
    Process a chat message through the agent chain.
    Handles FETCH: responses by calling fetch_people() and making follow-up invoke.
    Returns the final response text.
    """
    # Get or create agent chain/history for this session
    if session_id not in agent_sessions:
        LOGGER.debug("process_chat_message: creating new agent for session_id='%s'", session_id)
        runnable, history = create_agent(agent_name, location, listings)
        agent_sessions[session_id] = (runnable, history)
    else:
        LOGGER.debug("process_chat_message: reusing existing agent for session_id='%s'", session_id)
        runnable, history = agent_sessions[session_id]

    inputs = {
        "agent_name": agent_name,
        "location": location,
        "listings": ", ".join(listings),
        "question": question,
    }

    response = runnable.invoke(
        inputs,
        config={"configurable": {"session_id": session_id}},
    ).content.strip()

    if response.upper().startswith("FETCH:"):
        LOGGER.info(">>>>>>>> first invoke: %s", response)

        query = response[6:].strip()
        LOGGER.info("🔍 Fetching data for: %s", query)
        data = fetch_people(query)

        follow_up = (
            f"Here are the search results for '{query}': {data}\n"
            "Please summarise the key opportunities for the agent."
        )

        #LOGGER.debug("follow_up: %s\n", follow_up)

        response = runnable.invoke(
            {
                "agent_name": agent_name,
                "location": location,
                "listings": ", ".join(listings),
                "question": follow_up,
            },
            config={"configurable": {"session_id": session_id}},
        ).content.strip()
        LOGGER.info(">>>>>>>>>>> second invoke: %s:\n%s", follow_up, response)

    return response


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
        # Use hardcoded agent profile data
        agent_name = AGENT_NAME
        location = LOCATION
        listings = LISTINGS
        
        # Use agentId as session_id for conversation history
        session_id = request.agentId
        
        LOGGER.info("chat_endpoint: processing message for agentId='%s', session_id='%s'", request.agentId, session_id)
        
        # Process the chat message
        response_content = process_chat_message(
            agent_name=agent_name,
            location=location,
            listings=listings,
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
        
        return ChatResponse(message=message)
        
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
