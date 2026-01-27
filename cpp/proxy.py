"""Conversation controller/proxy for pacing management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .diagram_validator import (
    DiagramValidationResult,
    validate_diagram,
    should_hide_diagram,
)
from .llm import LLMClient
from .parser import Chunk, parse_chunks
from .prompts import load_upstream_prompt


class ConversationProxy:
    """Proxy that controls conversational pacing."""

    def __init__(
        self,
        llm_client: LLMClient,
        *,
        no_diagrams: bool = False,
        debug: bool = False,
    ):
        """Initialize the proxy.

        Args:
            llm_client: LLM client instance.
            no_diagrams: If True, always hide diagrams (e.g. --no-diagrams).
            debug: If True, store per-chunk debug info for validator decisions.
        """
        self.llm_client = llm_client
        self.no_diagrams = no_diagrams
        self.debug = debug
        self.user_prompt: Optional[str] = None
        self.chunks: List[Dict[str, Any]] = []
        self.current_index: int = 0
        self.upstream_model: str = llm_client.model

    def start_conversation(self, user_prompt: str) -> None:
        """Start a new conversation with the user prompt.

        Makes exactly one upstream LLM call, parses the response into chunks,
        validates diagrams, applies hide policy, and stores chunks.

        Args:
            user_prompt: The user's question or prompt.
        """
        self.user_prompt = user_prompt
        system_prompt = load_upstream_prompt(user_prompt)
        raw = self.llm_client.generate_raw(system_prompt)
        parsed = parse_chunks(raw)
        self.chunks = self._resolve_chunks(parsed)
        self.current_index = 0

    def _resolve_chunks(self, parsed: List[Chunk]) -> List[Dict[str, Any]]:
        """Apply diagram validation and hide policy; return storage chunks."""
        out: List[Dict[str, Any]] = []

        for c in parsed:
            idea_text = c.idea_text
            diagram_lines = c.diagram_lines
            diagram_display: Optional[str] = None
            debug_info: Optional[Dict[str, Any]] = None

            if self.no_diagrams:
                diagram_display = None
                if self.debug:
                    debug_info = {
                        "hidden": True,
                        "reason": "no-diagrams",
                        "extra_tokens": (),
                    }
            elif diagram_lines is None:
                diagram_display = None
                if self.debug:
                    debug_info = {
                        "hidden": False,
                        "reason": "none",
                        "extra_tokens": (),
                    }
            else:
                result: DiagramValidationResult = validate_diagram(
                    idea_text, diagram_lines
                )
                if should_hide_diagram(result):
                    diagram_display = None
                    if self.debug:
                        debug_info = {
                            "hidden": True,
                            "reason": "validation",
                            "extra_tokens": result.extra_tokens,
                        }
                else:
                    diagram_display = "\n".join(diagram_lines)
                    if self.debug:
                        debug_info = {
                            "hidden": False,
                            "reason": "ok",
                            "extra_tokens": (),
                        }

            chunk: Dict[str, Any] = {"idea": idea_text, "diagram": diagram_display}
            if self.debug and debug_info is not None:
                chunk["_debug"] = debug_info
            out.append(chunk)

        return out

    def get_current_chunk(self) -> Optional[Dict[str, Any]]:
        """Return the current chunk to display.

        Returns:
            Chunk dict with 'idea', 'diagram' (or None), and optional '_debug'.
        """
        if self.current_index < len(self.chunks):
            return self.chunks[self.current_index]
        return None

    def has_next(self) -> bool:
        """Return True if there are more chunks after the current one."""
        return self.current_index < len(self.chunks) - 1

    def next(self) -> bool:
        """Advance to the next chunk. Return True if advanced, False if at end."""
        if self.has_next():
            self.current_index += 1
            return True
        return False

    def go_deeper(self) -> None:
        """Placeholder for 'go deeper' (not implemented in v0)."""
        pass

    def switch_angle(self) -> None:
        """Placeholder for 'switch angle' (not implemented in v0)."""
        pass

    def get_session_state(self) -> dict:
        """Return current session state for debugging/inspection."""
        return {
            "user_prompt": self.user_prompt,
            "chunks": self.chunks,
            "current_index": self.current_index,
            "upstream_model": self.upstream_model,
            "total_chunks": len(self.chunks),
        }
