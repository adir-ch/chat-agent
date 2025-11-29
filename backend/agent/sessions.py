"""
Session management for the AI Agent service.
"""
from typing import Dict, Tuple
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from models import AgentProfile, TokenUsage

# Session management: maps agentId -> (runnable, history, profile, token_usage)
agent_sessions: Dict[str, Tuple[RunnableWithMessageHistory, ChatMessageHistory, AgentProfile, TokenUsage]] = {}

