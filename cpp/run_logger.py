"""Run logging functionality for persistent storage."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .prompts.loader import load_prompt_text, sha256


def create_run_dir(log_dir: Path, user_prompt: str) -> Path:
    """Create a new run directory with timestamp and slug.
    
    Args:
        log_dir: Base log directory (e.g., ./runs).
        user_prompt: User prompt for slug generation.
        
    Returns:
        Path to the created run directory.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate slug from prompt (first 30 chars, sanitized)
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in user_prompt[:30])
    slug = slug.strip("_") or "run"
    
    # Timestamp: YYYY-MM-DD_HHMMSS
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    
    run_name = f"{timestamp}_{slug}"
    run_path = log_dir / run_name
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "diagrams").mkdir(exist_ok=True)
    (run_path / "nlp_diagrams").mkdir(exist_ok=True)
    
    return run_path


def save_run_metadata(
    run_path: Path,
    user_prompt: str,
    explainer_model: str,
    visualizer_model: str,
    explainer_prompt_file: str,
    visualizer_prompt_file: str,
    diagram_policy: str,
    validator_enabled: bool,
    validator_max_extras: int,
    ideas: List[str],
    items: List[Dict[str, Any]],
    *,
    concept_map_generated: bool = False,
    concept_map_prompt_version: Optional[str] = None,
    concept_map_model: Optional[str] = None,
) -> None:
    """Save run.json metadata file.
    
    Args:
        run_path: Run directory path.
        user_prompt: Original user prompt.
        explainer_model: Model used for explainer.
        visualizer_model: Model used for visualizer.
        explainer_prompt_file: Path to explainer prompt file.
        visualizer_prompt_file: Path to visualizer prompt file.
        diagram_policy: Policy string (e.g., "eager").
        validator_enabled: Whether validator was enabled.
        validator_max_extras: Max extra tokens allowed.
        ideas: List of idea strings.
        items: List of item metadata dicts.
    """
    # Load prompt texts and compute hashes
    explainer_prompt_text = load_prompt_text(explainer_prompt_file)
    visualizer_prompt_text = load_prompt_text(visualizer_prompt_file)
    
    metadata = {
        "version": 2,
        "created_at": datetime.now().isoformat(),
        "user_prompt": user_prompt,
        "explainer": {
            "model": explainer_model,
            "prompt_file": explainer_prompt_file,
            "prompt_sha256": sha256(explainer_prompt_text),
        },
        "visualizer": {
            "model": visualizer_model,
            "prompt_file": visualizer_prompt_file,
            "prompt_sha256": sha256(visualizer_prompt_text),
        },
        "diagram_policy": diagram_policy,
        "validator": {
            "enabled": validator_enabled,
            "max_extras": validator_max_extras,
        },
        "ideas_count": len(ideas),
        "items": items,
    }
    
    # Add concept map fields if map was generated
    if concept_map_generated:
        metadata["concept_map_generated"] = True
        if concept_map_prompt_version:
            metadata["concept_map_prompt_version"] = concept_map_prompt_version
        if concept_map_model:
            metadata["concept_map_model"] = concept_map_model
    
    run_json_path = run_path / "run.json"
    with open(run_json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def save_explain_output(run_path: Path, explain_text: str) -> None:
    """Save raw explainer output to explain.txt.
    
    Args:
        run_path: Run directory path.
        explain_text: Raw explainer model output.
    """
    explain_path = run_path / "explain.txt"
    explain_path.write_text(explain_text, encoding="utf-8")


def save_ideas(run_path: Path, ideas: List[str]) -> None:
    """Save ideas list to ideas.json.
    
    Args:
        run_path: Run directory path.
        ideas: List of idea strings.
    """
    ideas_path = run_path / "ideas.json"
    with open(ideas_path, "w", encoding="utf-8") as f:
        json.dump(ideas, f, indent=2, ensure_ascii=False)


def save_diagram(run_path: Path, index: int, diagram_text: str) -> None:
    """Save diagram to diagrams/NNN.txt.
    
    Args:
        run_path: Run directory path.
        index: 1-based idea index.
        diagram_text: Diagram text (or "(none)").
    """
    diagram_path = run_path / "diagrams" / f"{index:03d}.txt"
    diagram_path.write_text(diagram_text, encoding="utf-8")


def save_nlp_diagram(run_path: Path, index: int, diagram_text: Optional[str]) -> None:
    """Save NLP shadow diagram to nlp_diagrams/NNN.txt.
    
    Args:
        run_path: Path to run directory.
        index: 1-based idea index.
        diagram_text: Diagram text or None (will write "(none)").
    """
    nlp_diagram_path = run_path / "nlp_diagrams" / f"{index:03d}.txt"
    if diagram_text is None:
        nlp_diagram_path.write_text("(none)", encoding="utf-8")
    else:
        nlp_diagram_path.write_text(diagram_text, encoding="utf-8")


def save_concept_map(run_path: Path, concept_map_text: Optional[str]) -> None:
    """Save concept map to concept_map.txt.
    
    Args:
        run_path: Path to run directory.
        concept_map_text: Concept map text or None (will write "(none)").
    """
    concept_map_path = run_path / "concept_map.txt"
    if concept_map_text is None:
        concept_map_path.write_text("(none)", encoding="utf-8")
    else:
        concept_map_path.write_text(concept_map_text, encoding="utf-8")


def load_concept_map(run_path: Path) -> Optional[str]:
    """Load concept map from concept_map.txt.
    
    Args:
        run_path: Run directory path.
        
    Returns:
        Concept map text, or None if file doesn't exist or is "(none)".
    """
    concept_map_path = run_path / "concept_map.txt"
    if not concept_map_path.exists():
        return None
    
    text = concept_map_path.read_text(encoding="utf-8").strip()
    if not text or text == "(none)":
        return None
    
    return text


def load_run_metadata(run_path: Path) -> Dict[str, Any]:
    """Load run.json metadata.
    
    Args:
        run_path: Run directory path.
        
    Returns:
        Metadata dict.
        
    Raises:
        FileNotFoundError: If run.json doesn't exist.
    """
    run_json_path = run_path / "run.json"
    if not run_json_path.exists():
        raise FileNotFoundError(f"run.json not found in {run_path}")
    
    with open(run_json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_ideas(run_path: Path) -> List[str]:
    """Load ideas from ideas.json.
    
    Args:
        run_path: Run directory path.
        
    Returns:
        List of idea strings.
        
    Raises:
        FileNotFoundError: If ideas.json doesn't exist.
    """
    ideas_path = run_path / "ideas.json"
    if not ideas_path.exists():
        raise FileNotFoundError(f"ideas.json not found in {run_path}")
    
    with open(ideas_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_diagram(run_path: Path, index: int) -> Optional[str]:
    """Load diagram from diagrams/NNN.txt.
    
    Args:
        run_path: Run directory path.
        index: 1-based idea index.
        
    Returns:
        Diagram text, or None if file doesn't exist.
    """
    diagram_path = run_path / "diagrams" / f"{index:03d}.txt"
    if not diagram_path.exists():
        return None
    
    return diagram_path.read_text(encoding="utf-8").strip()
