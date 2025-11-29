"""
Data models for the AI Agent service.
"""
from dataclasses import dataclass


class AgentProfile:
    """Agent profile data structure."""
    def __init__(self, agent_id: str, agent_name: str, location: str, listings: list[str]):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.location = location
        self.listings = listings


@dataclass
class TokenUsage:
    """Token usage tracking for a session."""
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

