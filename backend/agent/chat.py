from typing import Callable, Optional, Tuple, AsyncIterator
import time
import asyncio

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

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


# ----------------------------------------------------------
# Streaming Chat Processing Logic
# ----------------------------------------------------------

class TokenStreamHandler(AsyncCallbackHandler):
    """Callback handler that yields tokens as they arrive."""
    
    def __init__(self):
        super().__init__()
        self.token_queue = asyncio.Queue()
        self.done = False
        self.final_response = None
        
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when a new token is generated."""
        await self.token_queue.put(("token", token))
        
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called when LLM finishes generating."""
        self.final_response = response
        self.done = True
        await self.token_queue.put(("done", None))
        
    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM encounters an error."""
        self.done = True
        await self.token_queue.put(("error", str(error)))
        
    async def get_tokens(self) -> AsyncIterator[str]:
        """Async generator that yields tokens as they arrive."""
        while True:
            item = await self.token_queue.get()
            if item[0] == "token":
                yield item[1]
            elif item[0] == "done":
                break
            elif item[0] == "error":
                raise Exception(f"LLM error: {item[1]}")


async def process_chat_message_stream(
    profile: AgentProfile,
    question: str,
    session_id: str,
    create_llm: Callable,
    process_fetch_data: Optional[Callable[[str, str], str]] = None
) -> AsyncIterator[Tuple[str, int, int]]:
    """
    Process a chat message through the agent chain with streaming.
    Yields tokens as they arrive from the LLM.
    Handles FETCH: responses by calling fetch_people() and making follow-up stream.
    
    Args:
        profile: Agent profile
        question: User's question
        session_id: Session identifier
        create_llm: Function that creates and returns an LLM instance
        process_fetch_data: Optional function to process fetched data (e.g., for embeddings)
    
    Yields:
        Tuple[str, int, int]: (token_chunk, current_input_tokens, current_output_tokens)
        Token counts are cumulative and updated as generation progresses.
    """
    # Get or create agent chain/history for this session
    if session_id not in agent_sessions:
        LOGGER.debug("process_chat_message_stream: creating new agent for session_id='%s'", session_id)
        runnable, history = create_agent(
            profile.agent_name,
            profile.location,
            profile.listings,
            create_llm
        )
        token_usage = TokenUsage()
        agent_sessions[session_id] = (runnable, history, profile, token_usage)
    else:
        LOGGER.debug("process_chat_message_stream: reusing existing agent for session_id='%s'", session_id)
        runnable, history, _, token_usage = agent_sessions[session_id]
        # Update profile in case it changed
        agent_sessions[session_id] = (runnable, history, profile, token_usage)

    inputs = {
        "agent_name": profile.agent_name,
        "location": profile.location,
        "listings": ", ".join(profile.listings) if profile.listings else "",
        "question": question,
    }

    LOGGER.info("process_chat_message_stream: inputs=%s", inputs['question'])
    
    # Track cumulative token counts for this request
    request_input_tokens = 0
    request_output_tokens = 0
    accumulated_response = ""

    # Create callback handler for streaming
    callback_handler = TokenStreamHandler()
    
    # First stream with LangSmith trace context
    start_time = time.time()
    
    # Use astream() for streaming with callback handler
    config = {
        "configurable": {"session_id": session_id},
        "tags": ["chat-agent", f"agent-{profile.agent_id}", "first-invoke", "streaming"],
        "metadata": {
            "agent_id": profile.agent_id,
            "agent_name": profile.agent_name,
            "location": profile.location,
        },
        "run_name": f"chat-{session_id}-initial-stream",
        "callbacks": [callback_handler],
    }
    
    # Start streaming - astream yields chunks, but tokens come via callback
    async def stream_agent():
        async for chunk in runnable.astream(inputs, config=config):
            # Chunks from astream are typically the full response parts
            # But tokens come via callback handler
            pass
    
    # Run streaming and token collection concurrently
    stream_task = asyncio.create_task(stream_agent())
    
    # Yield tokens as they arrive from callback
    async for token in callback_handler.get_tokens():
        accumulated_response += token
        # Yield token chunk (we'll calculate tokens at the end)
        yield (token, 0, 0)  # Token counts will be calculated after completion
    
    # Wait for stream to complete
    await stream_task
    
    elapsed_time = time.time() - start_time
    LOGGER.info("Model response time (first stream): %.3f seconds", elapsed_time)
    response = accumulated_response.strip()
    
    # Track token usage from callback handler's final response
    # LLMResult has llm_output which contains token_usage
    if callback_handler.final_response and hasattr(callback_handler.final_response, 'llm_output'):
        llm_output = callback_handler.final_response.llm_output
        if llm_output and 'token_usage' in llm_output:
            token_info = llm_output['token_usage']
            input_tokens1 = token_info.get('prompt_tokens', token_info.get('input_tokens', 0))
            output_tokens1 = token_info.get('completion_tokens', token_info.get('output_tokens', 0))
            token_usage.add(input_tokens1, output_tokens1)
            request_input_tokens += input_tokens1
            request_output_tokens += output_tokens1
            LOGGER.info("Token usage (first stream): input=%d, output=%d", input_tokens1, output_tokens1)
        else:
            # Estimate tokens (rough approximation: ~4 chars per token)
            estimated_output_tokens = len(response) // 4
            request_output_tokens += estimated_output_tokens
    else:
        # Estimate tokens (rough approximation: ~4 chars per token)
        estimated_output_tokens = len(response) // 4
        request_output_tokens += estimated_output_tokens

    if response.upper().startswith("FETCH"):
        LOGGER.info(">>>>>>>> first stream: %s", response)

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

        # Second stream with LangSmith trace context
        start_time2 = time.time()
        accumulated_response2 = ""
        
        callback_handler2 = TokenStreamHandler()
        config2 = {
            "configurable": {"session_id": session_id},
            "tags": ["chat-agent", f"agent-{profile.agent_id}", "second-invoke", "fetch-followup", "streaming"],
            "metadata": {
                "agent_id": profile.agent_id,
                "agent_name": profile.agent_name,
                "location": profile.location,
                "query": query,
            },
            "run_name": f"chat-{session_id}-followup-stream",
            "callbacks": [callback_handler2],
        }
        
        async def stream_agent2():
            async for chunk in runnable.astream(
                {
                    "agent_name": profile.agent_name,
                    "location": profile.location,
                    "listings": ", ".join(profile.listings) if profile.listings else "",
                    "question": follow_up,
                },
                config=config2
            ):
                pass
        
        stream_task2 = asyncio.create_task(stream_agent2())
        
        # Yield tokens from second stream
        async for token in callback_handler2.get_tokens():
            accumulated_response2 += token
            yield (token, 0, 0)
        
        await stream_task2
            
        elapsed_time2 = time.time() - start_time2
        LOGGER.info("Model response time (second stream): %.3f seconds", elapsed_time2)
        response = accumulated_response2.strip()
        
        # Track token usage from second stream
        if callback_handler2.final_response and hasattr(callback_handler2.final_response, 'llm_output'):
            llm_output2 = callback_handler2.final_response.llm_output
            if llm_output2 and 'token_usage' in llm_output2:
                token_info2 = llm_output2['token_usage']
                input_tokens2 = token_info2.get('prompt_tokens', token_info2.get('input_tokens', 0))
                output_tokens2 = token_info2.get('completion_tokens', token_info2.get('output_tokens', 0))
                token_usage.add(input_tokens2, output_tokens2)
                request_input_tokens += input_tokens2
                request_output_tokens += output_tokens2
                LOGGER.info("Token usage (second stream): input=%d, output=%d", input_tokens2, output_tokens2)
            else:
                estimated_output_tokens2 = len(response) // 4
                request_output_tokens += estimated_output_tokens2
        else:
            estimated_output_tokens2 = len(response) // 4
            request_output_tokens += estimated_output_tokens2
        
        LOGGER.info(">>>>>>>>>>> second stream: %s:\n%s", follow_up, response)
    
    # Yield final token counts
    yield ("", request_input_tokens, request_output_tokens)

