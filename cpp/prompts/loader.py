"""Load prompt templates with {{USER_PROMPT}} or {{IDEA_TEXT}} substitution."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Tuple


def load_prompt_text(relative_path: str) -> str:
    """Load prompt text from package or repo root.
    
    Args:
        relative_path: Relative path like "prompts/explainer_v1.md"
        
    Returns:
        Prompt text as string.
        
    Raises:
        FileNotFoundError: If prompt cannot be found.
    """
    # Try package first (when installed)
    try:
        import importlib.resources as res
        # Convert "prompts/explainer_v1.md" -> "cpp.prompts" + "explainer_v1.md"
        parts = relative_path.split("/")
        if len(parts) == 2 and parts[0] == "prompts":
            return res.read_text("cpp.prompts", parts[1])
    except Exception:
        pass
    
    # Fallback: repo root
    try:
        # cpp/prompts/loader.py -> cpp/prompts -> cpp -> repo root
        base = Path(__file__).resolve().parent.parent.parent
        path = base / relative_path
        if path.is_file():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    
    raise FileNotFoundError(
        f"Could not find {relative_path}. "
        "Ensure the package is installed or run from repo root."
    )


def sha256(text: str) -> str:
    """Compute SHA256 hash of text as hex string.
    
    Args:
        text: Input text.
        
    Returns:
        Hex string of SHA256 hash.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_upstream_prompt(user_query: str) -> Tuple[str, str]:
    """Load upstream prompt template and split into system instructions and user message.
    
    DEPRECATED: Use load_explainer_prompt and load_visualizer_prompt instead.
    Kept for backward compatibility.
    
    Splits the template at "## User question" section:
    - System: everything before "## User question" (instructions)
    - User: the actual user query text
    
    Uses importlib.resources when installed as a package; falls back to
    repo-root ./prompts/ when running from source.
    
    Args:
        user_query: The user's question or prompt.
        
    Returns:
        Tuple of (system_prompt, user_message).
        
    Raises:
        FileNotFoundError: If template cannot be found.
    """
    template = load_prompt_text("prompts/upstream_prompt_template.md")
    
    # Split at "## User question" section
    parts = template.split("## User question")
    if len(parts) != 2:
        # Fallback: if no "## User question" marker, use entire template as system
        # and user_query as user message
        return (template.strip(), user_query)
    
    system_part = parts[0].strip()
    user_message = user_query
    
    return (system_part, user_message)


def load_explainer_prompt(user_query: str) -> Tuple[str, str]:
    """Load explainer prompt template and split into system and user messages.
    
    Args:
        user_query: The user's question or prompt.
        
    Returns:
        Tuple of (system_prompt, user_message).
    """
    template = load_prompt_text("prompts/explainer_v1.md")
    
    # Split at "User question:" marker
    parts = template.split("User question:")
    if len(parts) != 2:
        # Fallback: replace {{USER_PROMPT}} if present, or use entire template as system
        system_prompt = template.replace("{{USER_PROMPT}}", "").strip()
        return (system_prompt, user_query)
    
    system_part = parts[0].strip()
    user_message = user_query
    
    return (system_part, user_message)


def load_visualizer_prompt(idea_text: str) -> Tuple[str, str]:
    """Load visualizer prompt template and substitute idea text.
    
    Args:
        idea_text: The idea sentence to visualize.
        
    Returns:
        Tuple of (system_prompt, user_message).
    """
    template = load_prompt_text("prompts/visualizer_v1.md")
    
    # Replace {{IDEA_TEXT}} placeholder
    system_prompt = template.replace("{{IDEA_TEXT}}", idea_text)
    
    # The template is designed to be a single system message
    # Return as system prompt with empty user message
    return (system_prompt.strip(), "")
