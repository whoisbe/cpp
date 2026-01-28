"""Conversation controller/proxy for pacing management."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .diagram_validator import (
    DiagramValidationResult,
    validate_diagram,
    should_hide_diagram,
)
from .llm import LLMClient
from .parser import parse_ideas_only, parse_diagram_only
from .prompts.loader import load_explainer_prompt, load_visualizer_prompt


class ConversationProxy:
    """Proxy that controls conversational pacing."""

    def __init__(
        self,
        llm_client: LLMClient,
        *,
        no_diagrams: bool = False,
        debug: bool = False,
        log_dir: Optional[Path] = None,
        nlp_shadow: bool = True,
    ):
        """Initialize the proxy.

        Args:
            llm_client: LLM client instance.
            no_diagrams: If True, always hide diagrams (e.g. --no-diagrams).
            debug: If True, store per-chunk debug info for validator decisions.
            log_dir: Optional directory for run logging (if None, no logging).
            nlp_shadow: If True, enable shadow NLP diagram logging (default: True).
        """
        self.llm_client = llm_client
        self.no_diagrams = no_diagrams
        self.debug = debug
        self.log_dir = log_dir
        self.nlp_shadow = nlp_shadow
        self.user_prompt: Optional[str] = None
        self.ideas: List[str] = []
        self.diagram_cache: Dict[int, Optional[str]] = {}  # index -> diagram or None
        self.diagram_metadata: Dict[int, Dict[str, Any]] = {}  # index -> metadata
        self.current_index: int = 0
        self.explainer_model: str = llm_client.model
        self.visualizer_model: str = llm_client.model
        self.explain_raw: Optional[str] = None
        self.run_path: Optional[Path] = None

    def start_conversation(self, user_prompt: str) -> None:
        """Start a new conversation with the user prompt.

        Makes EXPLAIN call to get ideas only, then initializes for eager diagram generation.

        Args:
            user_prompt: The user's question or prompt.
        """
        self.user_prompt = user_prompt
        self.current_index = 0
        self.diagram_cache = {}
        self.diagram_metadata = {}

        # Create run directory if logging enabled
        if self.log_dir:
            from .run_logger import create_run_dir
            self.run_path = create_run_dir(self.log_dir, user_prompt)

        # EXPLAIN call: ideas only
        system_prompt, user_message = load_explainer_prompt(user_prompt)
        self.explain_raw = self.llm_client.generate_raw(system_prompt, user_message)
        self.ideas = parse_ideas_only(self.explain_raw)

        # Save explain output if logging
        if self.run_path and self.explain_raw:
            from .run_logger import save_explain_output, save_ideas
            save_explain_output(self.run_path, self.explain_raw)
            save_ideas(self.run_path, self.ideas)

    def _generate_diagram(self, idea_index: int) -> Optional[str]:
        """Generate diagram for idea at given index (0-based).
        
        Caches result in memory. Returns None if diagram is "(none)" or hidden.
        
        Args:
            idea_index: 0-based index of the idea.
            
        Returns:
            Diagram text or None.
        """
        if idea_index in self.diagram_cache:
            return self.diagram_cache[idea_index]

        if idea_index >= len(self.ideas):
            return None

        idea_text = self.ideas[idea_index]

        # VISUALIZE call: diagram only
        system_prompt, _ = load_visualizer_prompt(idea_text)
        diagram_raw = self.llm_client.generate_raw(system_prompt, "")
        diagram_lines = parse_diagram_only(diagram_raw)

        # Track if diagram was generated (before validation)
        diagram_generated = diagram_lines is not None
        diagram_display: Optional[str] = None
        hidden_reason: Optional[str] = None
        extra_tokens: List[str] = []

        if self.no_diagrams:
            diagram_display = None
            hidden_reason = "flag_no_diagrams"
        elif diagram_lines is None:
            diagram_display = None
            hidden_reason = None  # Not hidden, just not generated
        else:
            # Validate diagram
            result: DiagramValidationResult = validate_diagram(idea_text, diagram_lines)
            if should_hide_diagram(result):
                diagram_display = None
                hidden_reason = "validator_extra_tokens"
                extra_tokens = list(result.extra_tokens)
            else:
                diagram_display = "\n".join(diagram_lines)
                hidden_reason = None

        # Cache result
        self.diagram_cache[idea_index] = diagram_display

        # Store metadata for logging
        self.diagram_metadata[idea_index] = {
            "diagram_generated": diagram_generated,
            "diagram_hidden": diagram_display is None and diagram_generated,
            "hidden_reason": hidden_reason,
            "extra_tokens": extra_tokens,
        }

        # Save diagram if logging
        if self.run_path:
            from .run_logger import save_diagram
            diagram_text = diagram_display if diagram_display else "(none)"
            save_diagram(self.run_path, idea_index + 1, diagram_text)

        return diagram_display

    def get_current_chunk(self) -> Optional[Dict[str, Any]]:
        """Return the current chunk to display.

        Eagerly generates diagram if not cached.

        Returns:
            Chunk dict with 'idea', 'diagram' (or None), and optional '_debug'.
        """
        if self.current_index >= len(self.ideas):
            return None

        idea_text = self.ideas[self.current_index]
        diagram = self._generate_diagram(self.current_index)

        chunk: Dict[str, Any] = {"idea": idea_text, "diagram": diagram}

        if self.debug:
            meta = self.diagram_metadata.get(self.current_index, {})
            debug_info = {
                "hidden": meta.get("diagram_hidden", False),
                "reason": meta.get("hidden_reason"),
                "extra_tokens": tuple(meta.get("extra_tokens", [])),
            }
            chunk["_debug"] = debug_info

        return chunk

    def has_next(self) -> bool:
        """Return True if there are more ideas after the current one."""
        return self.current_index < len(self.ideas) - 1

    def next(self) -> bool:
        """Advance to the next idea. Return True if advanced, False if at end."""
        if self.has_next():
            self.current_index += 1
            return True
        return False

    def previous(self) -> bool:
        """Go back to the previous idea. Return True if moved back, False if at start."""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def go_deeper(self) -> None:
        """Placeholder for 'go deeper' (not implemented in v0)."""
        pass

    def switch_angle(self) -> None:
        """Placeholder for 'switch angle' (not implemented in v0)."""
        pass

    def finalize_run(self) -> None:
        """Finalize run logging by writing run.json metadata."""
        if not self.run_path:
            return

        from .run_logger import save_run_metadata, save_nlp_diagram
        from .nlp_import import is_nlp_available, get_nlp_functions

        # Build items list
        items = []
        nlp_available = self.nlp_shadow and is_nlp_available()
        analyze_sentence, render_diagram = get_nlp_functions() if nlp_available else (None, None)
        
        for i in range(len(self.ideas)):
            meta = self.diagram_metadata.get(i, {})
            item = {
                "index": i + 1,  # 1-based
                "idea_text": self.ideas[i],
                "diagram_generated": meta.get("diagram_generated", False),
                "diagram_hidden": meta.get("diagram_hidden", False),
                "hidden_reason": meta.get("hidden_reason"),
                "extra_tokens": meta.get("extra_tokens", []),
            }
            
            # Compute NLP shadow data
            if nlp_available and analyze_sentence and render_diagram:
                idea_text = self.ideas[i]
                try:
                    analysis = analyze_sentence(idea_text)
                    lines = render_diagram(idea_text)
                    diagram_text = None if lines is None else "\n".join(lines)
                    
                    item["nlp"] = {
                        "attempted": True,
                        "diagram": diagram_text,
                        "diagram_kind": analysis.get("diagram_kind"),
                        "confidence": analysis.get("confidence"),
                        "reasons": analysis.get("reasons", []),
                    }
                    
                    # Save NLP diagram file
                    save_nlp_diagram(self.run_path, i + 1, diagram_text)
                except Exception:
                    # If NLP computation fails, mark as attempted but failed
                    item["nlp"] = {
                        "attempted": True,
                        "diagram": None,
                        "diagram_kind": None,
                        "confidence": None,
                        "reasons": [],
                    }
                    save_nlp_diagram(self.run_path, i + 1, None)
            else:
                item["nlp"] = {
                    "attempted": False,
                }
            
            items.append(item)

        save_run_metadata(
            run_path=self.run_path,
            user_prompt=self.user_prompt or "",
            explainer_model=self.explainer_model,
            visualizer_model=self.visualizer_model,
            explainer_prompt_file="prompts/explainer_v1.md",
            visualizer_prompt_file="prompts/visualizer_v1.md",
            diagram_policy="eager",
            validator_enabled=True,
            validator_max_extras=0,
            ideas=self.ideas,
            items=items,
        )

    def get_session_state(self) -> dict:
        """Return current session state for debugging/inspection."""
        return {
            "user_prompt": self.user_prompt,
            "ideas": self.ideas,
            "current_index": self.current_index,
            "explainer_model": self.explainer_model,
            "visualizer_model": self.visualizer_model,
            "total_ideas": len(self.ideas),
        }
