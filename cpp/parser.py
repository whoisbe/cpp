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


def parse_ideas_only(raw: str) -> List[str]:
    """Parse ideas-only response (no diagrams) into list of idea strings.
    
    Format per item:
        Idea <n>: <text>
    
    Args:
        raw: Raw LLM response text.
        
    Returns:
        List of idea text strings (no "Idea n:" prefix).
    """
    ideas: List[str] = []
    # Split by "Idea <n>:" markers (n = 1, 2, ...)
    blocks = re.split(r'(?=^Idea\s+\d+:)', raw.strip(), flags=re.MULTILINE)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        match = re.match(r'^Idea\s+\d+:\s*(.*)', block, re.DOTALL)
        if not match:
            continue
        
        idea_text = match.group(1).strip()
        if idea_text:
            ideas.append(idea_text)
    
    return ideas


def parse_diagram_only(raw: str) -> Optional[List[str]]:
    """Parse diagram-only response into list of diagram lines.
    
    Format:
        Diagram:
        <lines until blank> or (none)
    
    Args:
        raw: Raw LLM response text.
        
    Returns:
        List of diagram lines, or None if "(none)" or empty.
    """
    # Find "Diagram:" marker
    diagram_match = re.search(r'Diagram:\s*', raw, re.IGNORECASE)
    if not diagram_match:
        return None
    
    diagram_part = raw[diagram_match.end():].strip()
    
    if not diagram_part or re.match(r'^\(none\)\s*$', diagram_part, re.IGNORECASE):
        return None
    
    # Diagram runs until blank line (or end)
    lines = []
    for line in diagram_part.split('\n'):
        stripped = line.strip()
        if not stripped:
            break
        lines.append(stripped)
    
    return lines if lines else None


def parse_map_only(raw: str) -> Optional[str]:
    """Parse map-only response into map text string.
    
    Format:
        Map:
        <lines until blank> or (none)
    
    Args:
        raw: Raw LLM response text.
        
    Returns:
        Map text as string, or None if "(none)" or empty.
    """
    # Find "Map:" marker
    map_match = re.search(r'Map:\s*', raw, re.IGNORECASE)
    if not map_match:
        return None
    
    map_part = raw[map_match.end():].strip()
    
    if not map_part or re.match(r'^\(none\)\s*$', map_part, re.IGNORECASE):
        return None
    
    # Map runs until blank line (or end)
    lines = []
    for line in map_part.split('\n'):
        stripped = line.strip()
        if not stripped:
            break
        lines.append(stripped)
    
    return "\n".join(lines) if lines else None


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
