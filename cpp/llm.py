"""LLM integration module for upstream model calls."""

import os
import re
from typing import List, Optional, Dict, Any


class LLMClient:
    """Client for making upstream LLM calls."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """Initialize LLM client.
        
        Args:
            model: Model identifier (default: gpt-4o-mini)
            api_key: API key (defaults to OPENAI_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
    
    def generate_chunks(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Generate structured chunks from user prompt.
        
        Makes exactly one upstream LLM call and returns parsed chunks.
        
        Args:
            user_prompt: The user's question or prompt
            
        Returns:
            List of chunk dicts, each with 'idea' and optional 'diagram' keys
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required. Install with: pip install openai"
            )
        
        client = OpenAI(api_key=self.api_key)
        
        system_prompt = (
            "Answer the user's question using 6–10 short, self-contained ideas.\n\n"
            "For each idea, output in the following format:\n\n"
            "Idea: one sentence expressing exactly one idea (≤ 30 words)\n"
            "Diagram: an optional ASCII diagram that reuses only words or phrases from the Idea text, or `(none)` if not applicable\n\n"
            "Rules:\n"
            "* Each idea must stand on its own\n"
            "* Do not introduce new terminology in diagrams\n"
            "* Prefer structural or relational diagrams over labeled or numbered ones\n"
            "* If unsure, omit the diagram\n"
            "* Do not include summaries or conclusions"
        )
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content.strip()
        chunks = self._parse_structured_chunks(content)
        
        return chunks
    
    def _parse_structured_chunks(self, content: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured chunks with ideas and diagrams.
        
        Parses format:
        Idea: [text]
        Diagram: [diagram lines or (none)]
        
        Args:
            content: Raw LLM response text
            
        Returns:
            List of chunk dicts with 'idea' and optional 'diagram' keys
        """
        chunks = []
        
        # Split by "Idea:" markers
        idea_blocks = re.split(r'(?=^Idea:)', content, flags=re.MULTILINE)
        
        for block in idea_blocks:
            block = block.strip()
            if not block or not block.startswith('Idea:'):
                continue
            
            lines = block.split('\n')
            idea_text = None
            diagram_lines = []
            in_diagram = False
            
            for line in lines:
                line_stripped = line.strip()
                
                # Extract idea text
                if line_stripped.startswith('Idea:'):
                    idea_text = line_stripped[5:].strip()  # Remove "Idea:" prefix
                    continue
                
                # Check for diagram marker
                if line_stripped.startswith('Diagram:'):
                    diagram_content = line_stripped[8:].strip()  # Remove "Diagram:" prefix
                    if diagram_content.lower() == '(none)':
                        # Explicitly no diagram
                        in_diagram = False
                    elif diagram_content:
                        # Diagram starts on same line
                        in_diagram = True
                        diagram_lines.append(diagram_content)
                    else:
                        # Diagram marker with no content, might be on next lines
                        in_diagram = True
                    continue
                
                # Collect diagram lines
                if in_diagram:
                    if line_stripped:
                        diagram_lines.append(line_stripped)
                    # Stop if we hit another Idea: marker (shouldn't happen with proper splitting, but safety check)
                    if line_stripped.startswith('Idea:'):
                        break
            
            # Create chunk dict
            if idea_text:
                chunk = {'idea': idea_text}
                
                # Process diagram if present
                if diagram_lines:
                    diagram = '\n'.join(diagram_lines)
                    # Validate and clean diagram (check format and content)
                    validated_diagram = self._validate_diagram(diagram, idea_text)
                    if validated_diagram:
                        chunk['diagram'] = validated_diagram
                    else:
                        chunk['diagram'] = None
                else:
                    chunk['diagram'] = None
                
                chunks.append(chunk)
        
        # Fallback: if no structured format found, try old parsing
        if not chunks:
            return self._fallback_parse(content)
        
        return chunks
    
    def _validate_diagram(self, diagram: str, idea_text: str) -> Optional[str]:
        """Validate and clean diagram according to spec constraints.
        
        Enforces "Text is the source of truth" rule: diagrams may only reuse
        terms/phrases that appear verbatim in the idea text.
        
        Args:
            diagram: Raw diagram text
            idea_text: The idea text that the diagram must derive from
            
        Returns:
            Validated diagram string, or None if invalid or introduces new terms
        """
        if not diagram:
            return None
        
        lines = diagram.split('\n')
        
        # Enforce 8-line limit
        if len(lines) > 8:
            lines = lines[:8]
        
        # Allowed characters: -|/\<>[]()_ plus spaces and alphanumeric
        allowed_chars = set('-|/\\<>[]()_ ') | set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        validated_lines = []
        for line in lines:
            # Check if line contains only allowed characters
            if all(c in allowed_chars for c in line):
                validated_lines.append(line)
            else:
                # Filter out invalid characters, keep allowed ones
                filtered = ''.join(c if c in allowed_chars else ' ' for c in line)
                if filtered.strip():  # Only add if there's content after filtering
                    validated_lines.append(filtered)
        
        result = '\n'.join(validated_lines).strip()
        if not result:
            return None
        
        # Check if diagram introduces new terms not in idea text
        if not self._diagram_uses_only_idea_terms(result, idea_text):
            return None  # Reject diagram that introduces new terminology
        
        return result
    
    def _diagram_uses_only_idea_terms(self, diagram: str, idea_text: str) -> bool:
        """Check if diagram only uses terms from the idea text.
        
        Extracts meaningful words from diagram and verifies they appear in idea text.
        Allows structural characters and common connectors.
        
        Args:
            diagram: The diagram text to validate
            idea_text: The source idea text
            
        Returns:
            True if diagram only uses terms from idea text, False otherwise
        """
        # Normalize both texts to lowercase for comparison
        idea_lower = idea_text.lower()
        diagram_lower = diagram.lower()
        
        # Extract words from idea text (alphanumeric sequences)
        idea_words = set(re.findall(r'\b[a-z0-9]+\b', idea_lower))
        
        # Extract words from diagram (alphanumeric sequences)
        diagram_words = set(re.findall(r'\b[a-z0-9]+\b', diagram_lower))
        
        # Remove very common structural/connector words that are acceptable
        # These are typically part of diagram structure, not content
        structural_words = {
            'a', 'an', 'the', 'and', 'or', 'to', 'from', 'of', 'in', 'on', 'at',
            'by', 'for', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall'
        }
        
        # Filter out structural words and single characters (likely diagram elements)
        diagram_content_words = {
            word for word in diagram_words 
            if word not in structural_words and len(word) > 1
        }
        
        # If no content words in diagram (only structural), it's valid
        if not diagram_content_words:
            return True
        
        # Check if all diagram content words appear in idea text
        # Allow partial matches (e.g., "prompt" matches "prompts")
        for diagram_word in diagram_content_words:
            # Check exact match first
            if diagram_word in idea_words:
                continue
            
            # Check if any idea word contains this word (for plurals, etc.)
            # or if this word is a substring of any idea word
            found = False
            for idea_word in idea_words:
                if diagram_word in idea_word or idea_word in diagram_word:
                    found = True
                    break
            
            if not found:
                # Check for phrase matches (multi-word terms)
                # Look for the word as part of a phrase in the idea text
                if diagram_word in idea_lower:
                    continue
                
                # Word not found in idea text - diagram introduces new terminology
                return False
        
        return True
    
    def _fallback_parse(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser for malformed responses.
        
        Attempts to extract ideas from unstructured text.
        
        Args:
            content: Raw LLM response text
            
        Returns:
            List of chunk dicts with 'idea' and 'diagram' keys
        """
        chunks = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet markers and numbering
            for prefix in ['- ', '* ', '• ', '· ', '→ ', '→']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            
            # Remove numbered bullets (1., 2., etc.)
            if line and line[0].isdigit():
                parts = line.split('.', 1)
                if len(parts) == 2:
                    line = parts[1].strip()
            
            if line:
                chunks.append({'idea': line, 'diagram': None})
        
        # If no bullets found, try splitting by sentences
        if not chunks:
            sentences = re.split(r'[.!?]+\s+', content)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    chunks.append({'idea': sentence, 'diagram': None})
        
        # If still nothing, use entire content as one idea
        if not chunks:
            chunks.append({'idea': content, 'diagram': None})
        
        return chunks
