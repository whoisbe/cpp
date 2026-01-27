"""LLM integration module for upstream model calls."""

from __future__ import annotations

import os
from typing import Optional


class LLMClient:
    """Client for making upstream LLM calls."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            model: Model identifier (default: gpt-4o-mini).
            api_key: API key (defaults to OPENAI_API_KEY env var).
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def generate_raw(self, system_prompt: str) -> str:
        """Call upstream LLM with the given system prompt and return raw response text.

        Makes exactly one upstream LLM call. No parsing or validation.

        Args:
            system_prompt: Full system message (e.g. rendered upstream template).

        Returns:
            Raw response text from the model.
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        client = OpenAI(api_key=self.api_key)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Proceed."},
            ],
            temperature=0.7,
        )

        return (response.choices[0].message.content or "").strip()
