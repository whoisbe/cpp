"""
diagram_validator.py — minimal heuristic validator for CPP

Goal: detect diagrams that introduce new terminology not present in the Idea line.

This is intentionally *domain-agnostic* and lightweight:
- Extract allowed tokens from the Idea line
- Extract used tokens from the Diagram block
- Flag if Diagram contains tokens not in the Idea (with a small stopword allowlist)

If invalid:
- Either hide diagram (prefer in v0)
- Or trigger a scoped “repair diagram only” LLM call (v0.1+)

Notes:
- This is a heuristic. It errs on the side of hiding diagrams.
- You can tune STOPWORDS as you observe false positives.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple


STOPWORDS: Set[str] = {
    # common glue words
    "a","an","the","and","or","to","of","in","on","for","by","with","as","at","from","into","over","than",
    "is","are","was","were","be","been","being","do","does","did",
    # diagram-ish tokens you may allow globally
    "input","output","user","model","data","system",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")  # words/numbers, simple

@dataclass(frozen=True)
class DiagramValidationResult:
    ok: bool
    extra_tokens: Tuple[str, ...]


def _tokens(text: str) -> List[str]:
    return TOKEN_RE.findall(text)


def validate_diagram(idea_line: str, diagram_lines: Iterable[str]) -> DiagramValidationResult:
    """
    idea_line: the Idea sentence (excluding the 'Idea n:' prefix is fine)
    diagram_lines: lines after 'Diagram:' (excluding the literal 'Diagram:' label line)

    Returns ok=True if diagram uses no new tokens beyond idea (plus STOPWORDS).
    """
    idea_tokens = {t.lower() for t in _tokens(idea_line)}
    diagram_tokens = [t.lower() for line in diagram_lines for t in _tokens(line)]

    extras = sorted({t for t in diagram_tokens if t not in idea_tokens and t not in STOPWORDS})
    return DiagramValidationResult(ok=(len(extras) == 0), extra_tokens=tuple(extras))


def should_hide_diagram(result: DiagramValidationResult, max_extras: int = 0) -> bool:
    """
    In v0, hide if any extras.
    In future, you might allow a tiny number of extras (e.g., 1) if they’re harmless.
    """
    return (not result.ok) and (len(result.extra_tokens) > max_extras)


def _run_mini_tests() -> None:
    """Minimal unit-ish tests: 1st-hide and reuse-pass."""
    # 1. Diagram introduces "1st" when "1st" not in idea => should hide
    idea1 = "Overtones are any frequencies higher than the fundamental frequency, including harmonics."
    diagram1 = [
        "Fundamental",
        "|",
        "1st Harmonic (1st Overtone)",
    ]
    res1 = validate_diagram(idea1, diagram1)
    assert not res1.ok and "1st" in res1.extra_tokens, f"expected hide: {res1}"
    assert should_hide_diagram(res1), "should_hide_diagram(1st case) should be True"
    print("1st-hide: ok")

    # 2. Diagram only reuses tokens from idea => should pass
    idea2 = "Harmonics and overtones relate to the fundamental frequency."
    diagram2 = [
        "Fundamental -> Harmonics",
        "     |",
        "  Overtones",
    ]
    res2 = validate_diagram(idea2, diagram2)
    assert res2.ok and len(res2.extra_tokens) == 0, f"expected pass: {res2}"
    assert not should_hide_diagram(res2), "should_hide_diagram(reuse case) should be False"
    print("reuse-pass: ok")


if __name__ == "__main__":
    _run_mini_tests()
