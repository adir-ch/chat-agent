from typing import Callable, Optional, Tuple
import time

from models import AgentProfile, TokenUsage
from utils import track_and_log_token_usage, fetch_people, mask_sensitive_data, LOGGER
from sessions import agent_sessions
from agent import create_agent
from prompts import format_follow_up


# ----------------------------------------------------------
# Chat Processing Logic
# ----------------------------------------------------------

def process_chat_message(
    profile: AgentProfile,
    question: str,
    session_id: str,
    create_llm: Callable,
    process_fetch_data: Optional[Callable[[str, str], str]] = None
) -> Tuple[str, int, int]:
    """
    Process a chat message through the agent chain.
    Handles FETCH: responses by calling fetch_people() and making follow-up invoke.
    
    Args:
        profile: Agent profile
        question: User's question
        session_id: Session identifier
        create_llm: Function that creates and returns an LLM instance
        process_fetch_data: Optional function to process fetched data (e.g., for embeddings)
    
    Returns:
        Tuple[str, int, int]: (response_text, total_input_tokens, total_output_tokens)
        Token counts are cumulative for all invocations in this request.
    """
    # Get or create agent chain/history for this session
    if session_id not in agent_sessions:
        LOGGER.debug("process_chat_message: creating new agent for session_id='%s'", session_id)
        runnable, history = create_agent(
            profile.agent_name,
            profile.location,
            profile.listings,
            create_llm
        )
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
    start_time = time.time()
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
    elapsed_time = time.time() - start_time
    LOGGER.info("Model response time (first invoke): %.3f seconds", elapsed_time)
    response = response_obj.content.strip()
    
    # Track and log token usage, accumulate for this request
    input_tokens1, output_tokens1 = track_and_log_token_usage(response_obj, token_usage, session_id, "first invoke")
    request_input_tokens += input_tokens1
    request_output_tokens += output_tokens1

    if response.upper().startswith("FETCH"):
        LOGGER.info(">>>>>>>> first invoke: %s", response)

        query = response[6:].strip()
        LOGGER.info("🔍 Fetching data for: %s", query)
        data = fetch_people(query)
        LOGGER.info("Data Received size: %d", len(data))

        # Process fetched data (e.g., apply embeddings, mask sensitive data)
        if process_fetch_data:
            processed_data = process_fetch_data(data, query)
        else:
            # Default: mask sensitive data
            processed_data = mask_sensitive_data(data)

        follow_up = format_follow_up(query, processed_data)

        # Second invoke with LangSmith trace context
        start_time2 = time.time()
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
        elapsed_time2 = time.time() - start_time2
        LOGGER.info("Model response time (second invoke): %.3f seconds", elapsed_time2)
        response = response_obj2.content.strip()
        
        # Track and log token usage, accumulate for this request
        input_tokens2, output_tokens2 = track_and_log_token_usage(response_obj2, token_usage, session_id, "second invoke")
        request_input_tokens += input_tokens2
        request_output_tokens += output_tokens2
        LOGGER.info(">>>>>>>>>>> second invoke: %s:\n%s", follow_up, response)

    return response, request_input_tokens, request_output_tokens

