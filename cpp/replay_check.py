"""Minimal self-check for replay functionality."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .run_logger import (
    create_run_dir,
    save_run_metadata,
    save_ideas,
    save_diagram,
    load_run_metadata,
    load_ideas,
    load_diagram,
)


def test_replay_functionality() -> None:
    """Test that replay can load and navigate a minimal run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "runs"
        
        # Create a minimal run
        run_path = create_run_dir(log_dir, "Test question")
        
        # Save ideas
        ideas = [
            "First idea about testing.",
            "Second idea about validation.",
        ]
        save_ideas(run_path, ideas)
        
        # Save diagrams
        save_diagram(run_path, 1, "Diagram 1\n  |\n  v")
        save_diagram(run_path, 2, "(none)")
        
        # Save metadata
        items = [
            {
                "index": 1,
                "idea_text": ideas[0],
                "diagram_generated": True,
                "diagram_hidden": False,
                "hidden_reason": None,
                "extra_tokens": [],
            },
            {
                "index": 2,
                "idea_text": ideas[1],
                "diagram_generated": False,
                "diagram_hidden": False,
                "hidden_reason": None,
                "extra_tokens": [],
            },
        ]
        save_run_metadata(
            run_path=run_path,
            user_prompt="Test question",
            explainer_model="test-model",
            visualizer_model="test-model",
            explainer_prompt_file="prompts/explainer_v1.md",
            visualizer_prompt_file="prompts/visualizer_v1.md",
            diagram_policy="eager",
            validator_enabled=True,
            validator_max_extras=0,
            ideas=ideas,
            items=items,
        )
        
        # Test loading
        metadata = load_run_metadata(run_path)
        assert metadata["version"] == 1, "Version should be 1"
        assert metadata["ideas_count"] == 2, "Should have 2 ideas"
        assert len(metadata["items"]) == 2, "Should have 2 items"
        
        loaded_ideas = load_ideas(run_path)
        assert len(loaded_ideas) == 2, "Should load 2 ideas"
        assert loaded_ideas == ideas, "Ideas should match"
        assert len(loaded_ideas) == metadata["ideas_count"], "Ideas count should match"
        
        # Test diagram loading
        diagram1 = load_diagram(run_path, 1)
        assert diagram1 == "Diagram 1\n  |\n  v", "First diagram should load"
        
        diagram2 = load_diagram(run_path, 2)
        assert diagram2 == "(none)", "Second diagram should be (none)"
        
        # Test missing diagram
        diagram3 = load_diagram(run_path, 3)
        assert diagram3 is None, "Missing diagram should return None"
        
        print("✓ Replay functionality test passed!")


if __name__ == "__main__":
    test_replay_functionality()
