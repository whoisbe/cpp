"""Parse upstream LLM response into per-idea chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Chunk:
    """A single idea chunk with optional diagram lines."""

    index: int  # 1-based, matches "Idea <n>"
    idea_text: str
    diagram_lines: Optional[List[str]]  # None if no diagram or Diagram: (none)


def parse_chunks(raw: str) -> List[Chunk]:
    """Parse upstream multi-item response into List[Chunk].

    Format per item:
        Idea <n>: <text>
        Diagram: <lines until blank> or (none)

    "Diagram: (none)" or no Diagram block => diagram_lines is None.
    Diagram may be multi-line up to a blank line.

    Args:
        raw: Raw LLM response text.

    Returns:
        List of Chunk with index, idea_text, diagram_lines (or None).
    """
    chunks: List[Chunk] = []
    # Split by "Idea <n>:" markers (n = 1, 2, ...)
    blocks = re.split(r'(?=^Idea\s+\d+:)', raw.strip(), flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        match = re.match(r'^Idea\s+(\d+):\s*(.*)', block, re.DOTALL)
        if not match:
            continue

        n = int(match.group(1))
        rest = match.group(2).strip()

        # Find "Diagram:" (newline or space before it) and split idea vs diagram
        diagram_match = re.search(r'(?:\n| )Diagram:\s*', rest, re.IGNORECASE)
        if not diagram_match:
            idea_text = rest.strip()
            diagram_lines = None
        else:
            idea_text = rest[: diagram_match.start()].strip()
            diagram_part = rest[diagram_match.end() :].strip()

            if not diagram_part or re.match(r'^\(none\)\s*$', diagram_part, re.IGNORECASE):
                diagram_lines = None
            else:
                # Diagram runs until blank line (or end)
                lines = []
                for line in diagram_part.split('\n'):
                    stripped = line.strip()
                    if not stripped:
                        break
                    lines.append(stripped)
                diagram_lines = lines if lines else None

        chunks.append(Chunk(index=n, idea_text=idea_text, diagram_lines=diagram_lines))

    return chunks
