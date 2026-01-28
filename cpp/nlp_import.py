"""Guarded import helper for nlp_diagrammer.

This module provides a safe way to import nlp_diagrammer, which is a sibling
package in the workspace. It handles import errors gracefully.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from nlp_diagrammer.nlp_diagrammer.heuristics import analyze_sentence  # type: ignore
    from nlp_diagrammer.nlp_diagrammer.diagrammer import render_diagram  # type: ignore

# Try to import nlp_diagrammer
_nlp_available = False
_import_error: Optional[Exception] = None
analyze_sentence = None
render_diagram = None

try:
    # First try direct import (works if installed or in workspace)
    import nlp_diagrammer
    from nlp_diagrammer.nlp_diagrammer.heuristics import analyze_sentence
    from nlp_diagrammer.nlp_diagrammer.diagrammer import render_diagram
    _nlp_available = True
except ImportError as e1:
    # Fallback: add repo root to sys.path (so nlp_diagrammer package can be found)
    try:
        # cpp/nlp_import.py -> cpp -> repo root
        base = Path(__file__).resolve().parent.parent
        nlp_path = base / "nlp_diagrammer"
        if nlp_path.exists() and nlp_path.is_dir():
            # Add repo root to sys.path so "import nlp_diagrammer" works
            if str(base) not in sys.path:
                sys.path.insert(0, str(base))
            import nlp_diagrammer
            from nlp_diagrammer.nlp_diagrammer.heuristics import analyze_sentence
            from nlp_diagrammer.nlp_diagrammer.diagrammer import render_diagram
            _nlp_available = True
    except Exception as e2:
        _import_error = e2


def is_nlp_available() -> bool:
    """Check if nlp_diagrammer is available for import."""
    return _nlp_available


def get_nlp_functions():
    """Get nlp_diagrammer functions if available, otherwise return None."""
    if _nlp_available:
        return analyze_sentence, render_diagram
    return None, None
