import re

ALLOWED_GLUE = {
    'priority:', 'constraints:', '|', '->', ',', ':'
}

def clean_text(text: str) -> str:
    """Standardize whitespace."""
    return ' '.join(text.strip().split())

def is_glue_or_token(word: str, tokens: set[str]) -> bool:
    """Check if word is allowed glue or in allowed usage tokens."""
    return word.lower() in ALLOWED_GLUE or word.lower() in tokens

def center_text(text: str, width: int) -> str:
    """Center text within a fixed width."""
    if len(text) >= width:
        return text[:width]
    padding = (width - len(text)) // 2
    return " " * padding + text + " " * (width - len(text) - padding)

def format_box(text: str, width: int = 20, style: str = "box") -> list[str]:
    """Create a simple ASCII box around text."""
    # Truncate if too long to fit in 1 line inside box
    inner_width = width - 2
    if len(text) > inner_width:
        text = text[:inner_width-3] + "..."
    
    centered = center_text(text, inner_width)
    if style == "round":
        return [
            f"/{'-'*inner_width}\\",
            f"|{centered}|",
            f"\\{'-'*inner_width}/"
        ]
    return [
        f"+{'-'*inner_width}+",
        f"|{centered}|",
        f"+{'-'*inner_width}+"
    ]

