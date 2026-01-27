"""Conversation controller/proxy for pacing management."""

from typing import List, Optional, Dict, Any
from .llm import LLMClient


class ConversationProxy:
    """Proxy that controls conversational pacing."""
    
    def __init__(self, llm_client: LLMClient):
        """Initialize conversation proxy.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
        self.user_prompt: Optional[str] = None
        self.chunks: List[Dict[str, Any]] = []
        self.current_index: int = 0
        self.upstream_model: str = llm_client.model
    
    def start_conversation(self, user_prompt: str) -> None:
        """Start a new conversation with user prompt.
        
        Makes exactly one upstream LLM call and stores chunks.
        
        Args:
            user_prompt: The user's question or prompt
        """
        self.user_prompt = user_prompt
        self.chunks = self.llm_client.generate_chunks(user_prompt)
        self.current_index = 0
    
    def get_current_chunk(self) -> Optional[Dict[str, Any]]:
        """Get the current chunk to display.
        
        Returns:
            Current chunk dict with 'idea' and optional 'diagram' keys, or None if no more chunks
        """
        if self.current_index < len(self.chunks):
            return self.chunks[self.current_index]
        return None
    
    def has_next(self) -> bool:
        """Check if there are more chunks available."""
        return self.current_index < len(self.chunks) - 1
    
    def next(self) -> bool:
        """Advance to next chunk.
        
        Returns:
            True if advanced, False if already at end
        """
        if self.has_next():
            self.current_index += 1
            return True
        return False
    
    def go_deeper(self) -> None:
        """Placeholder for 'go deeper' functionality (not implemented in v0)."""
        # Not implemented in v0 - placeholder
        pass
    
    def switch_angle(self) -> None:
        """Placeholder for 'switch angle' functionality (future)."""
        # Not implemented in v0 - placeholder
        pass
    
    def get_session_state(self) -> dict:
        """Get current session state (for debugging/inspection)."""
        return {
            "user_prompt": self.user_prompt,
            "chunks": self.chunks,
            "current_index": self.current_index,
            "upstream_model": self.upstream_model,
            "total_chunks": len(self.chunks)
        }
