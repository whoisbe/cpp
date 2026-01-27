"""Load upstream prompt template with {{USER_PROMPT}} substitution."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def _load_from_package() -> Optional[str]:
    """Load template via importlib.resources (works when installed)."""
    try:
        import importlib.resources as res
        return res.read_text("cpp.prompts", "upstream_prompt_template.md")
    except Exception:
        return None


def _load_from_repo_root() -> Optional[str]:
    """Fallback: load from repo ./prompts/ when running from source."""
    try:
        # cpp/prompts/loader.py -> cpp/prompts -> cpp -> repo root
        base = Path(__file__).resolve().parent.parent.parent
        path = base / "prompts" / "upstream_prompt_template.md"
        if path.is_file():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return None


def load_upstream_prompt(user_query: str) -> str:
    """Load upstream prompt template and replace {{USER_PROMPT}} with user query.

    Uses importlib.resources when installed as a package; falls back to
    repo-root ./prompts/ when running from source.

    Args:
        user_query: The user's question or prompt.

    Returns:
        Full prompt string (system message content).

    Raises:
        FileNotFoundError: If template cannot be found.
    """
    template = _load_from_package() or _load_from_repo_root()
    if not template:
        raise FileNotFoundError(
            "Could not find prompts/upstream_prompt_template.md. "
            "Ensure the package is installed or run from repo root."
        )
    return template.replace("{{USER_PROMPT}}", user_query)
