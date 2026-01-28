import re
from .utils import clean_text

# Heuristic Constants

# 1. Compare / Trade-off
COMPARE_MARKERS = {'vs', 'versus', 'whereas', 'while', 'but'}
PREFERENCE_MARKERS = {'over', 'rather than', 'instead of', 'more than', 'less than'}

# 2. Taxonomy / Categorization
TAXONOMY_MARKERS = {'can be', 'either', 'types of', 'classified as', 'category', 'kinds of'}
# "X are Y" pattern is harder with regex, handling via best-effort or specific phrasing if needed.
# For now, relying on explicit markers + simple pattern matching if applicable.

# 3. Part-whole / Composition
COMPOSITION_MARKERS = {'consists of', 'includes', 'contains', 'made of', 'composed of', 'has'}

# 4. Properties / Constraints
PROPERTY_VERBS = {'ensures', 'provides', 'offers', 'supports', 'enforces', 'guarantees', 'prioritizes'} # Added prioritizes which was in original diagrammer
PRIORITY_VERBS = PROPERTY_VERBS # Alias for diagrammer compatibility
CONSTRAINT_PHRASES = {'without', 'with'} # "in <noun>" is cautious

# 5. Role Differentiation
# Harder to capture with simple sets, relies on structure analysis (two agents, parallelism).

# Anti-signals
ANTI_ADJECTIVES = {'important', 'critical', 'matters', 'essential'} # + "is/are"
IDIOM_DENYLIST = {'safety first', 'security first', 'less is more'}
MECHANISM_MARKERS = {'first', 'then', 'next', 'after', 'before', 'until', 'because', 'so that', 'therefore'}


def analyze_sentence(text: str) -> dict:
    """
    Analyze a sentence to determine if it is diagram-worthy and what kind of diagram it fits.
    
    Returns:
        {
          "diagram_worthy": bool,
          "diagram_kind": "compare" | "category" | "priority" | None,
          "confidence": float,
          "reasons": [str, ...]
        }
    """
    clean = clean_text(text)
    # preserve original casing for some heuristics if needed, but mostly lowered for keywords
    lower_text = clean.lower()
    words = lower_text.split()
    
    reasons = []
    
    # --- 1. Anti-Signal Checks (Preliminary) ---
    # We'll flag them but might not return immediately if we want to log reasons.
    # But specced: "Apply anti-signals to downgrade to None" - usually applied at end or overrides positive signals.
    
    # B) Idioms / slogans
    # very short (<= 4 tokens) AND contains slogan pattern
    token_count = len(words)
    if token_count <= 4:
        for idiom in IDIOM_DENYLIST:
            if idiom in lower_text:
                return {
                    "diagram_worthy": False,
                    "diagram_kind": None,
                    "confidence": 0.0,
                    "reasons": [f"Idiom detected: '{idiom}'"]
                }
    
    # C) Mechanism-heavy (temporal/process)
    # If mechanism markers present, heavy penalty or disqualify.
    mechanism_hits = [m for m in MECHANISM_MARKERS if m in words] # strict word match for some
    # Some markers like "first" might be valid in "Safety first" (idiom) but also "First, do X". 
    # The spec says "Mechanism-heavy ... v0 should not".
    if mechanism_hits:
         # We might allow it if it finds a STRONG signal elsewhere, but per spec "v0 should not".
         # Let's verify if mechanism markers are purely disqualifying. 
         # "Apply anti-signals to downgrade to None". So yes.
         return {
            "diagram_worthy": False,
            "diagram_kind": None,
            "confidence": 0.0,
            "reasons": [f"Mechanism/Process detected: {mechanism_hits}"]
        }

    # A) Pure assertions (Low structure)
    # "mostly adjectives + is/are" -> This is a bit fuzzy to detect without POS tagging.
    # We'll approximate: checks for "is/are" + abstract nouns/adjectives and NO other signals.
    # We will defer this to the "No signal found" case basically.
    
    
    # --- Positive Signals (Priority Order) ---
    
    # 1. Compare / Trade-off (HIGH)
    # specific markers
    has_compare = any(m in words for m in COMPARE_MARKERS)
    has_preference = any(p in lower_text for p in PREFERENCE_MARKERS) # phrases need text search
    
    if has_compare or has_preference:
        markers = [m for m in COMPARE_MARKERS if m in words] + \
                  [p for p in PREFERENCE_MARKERS if p in lower_text]
        return {
            "diagram_worthy": True,
            "diagram_kind": "compare",
            "confidence": 0.9,
            "reasons": [f"Compare/Trade-off markers found: {markers}"]
        }
        
    # 2. Part-whole / Composition (HIGH) -> 'category'
    has_composition = any(m in lower_text for m in COMPOSITION_MARKERS)
    if has_composition:
        markers = [m for m in COMPOSITION_MARKERS if m in lower_text]
        return {
            "diagram_worthy": True,
            "diagram_kind": "category",
            "confidence": 0.85,
            "reasons": [f"Part-whole markers found: {markers}"]
        }
        
    # 3. Taxonomy / Categorization (HIGH) -> 'category'
    has_taxonomy = any(m in lower_text for m in TAXONOMY_MARKERS)
    # Check for "or" lists which might be categorization "A, B, or C"
    has_or_list = ' or ' in lower_text and ',' in lower_text
    
    if has_taxonomy or has_or_list:
        markers = [m for m in TAXONOMY_MARKERS if m in lower_text]
        if has_or_list: markers.append("list with 'or'")
        return {
            "diagram_worthy": True,
            "diagram_kind": "category",
            "confidence": 0.8,
            "reasons": [f"Taxonomy markers found: {markers}"]
        }
    
    # 4. Properties / Constraints (MEDIUM-HIGH) -> 'priority'
    # property verbs
    has_prop_verb = any(v in words for v in PROPERTY_VERBS)
    # constraint phrases
    has_constraint = any(c in words for c in CONSTRAINT_PHRASES)
    
    if has_prop_verb or has_constraint:
        markers = [v for v in PROPERTY_VERBS if v in words] + \
                  [c for c in CONSTRAINT_PHRASES if c in words]
        return {
            "diagram_worthy": True,
            "diagram_kind": "priority",
            "confidence": 0.7,
            "reasons": [f"Property/Constraint markers found: {markers}"]
        }
        
    # 5. Role differentiation (MEDIUM) -> 'compare'
    # "Clients ..., servers ..."
    # Look for: Noun ... , Noun ... pattern?
    # HEURISTIC: comma separation + distinct subjects? 
    # Simple proxy: if comma exists and we have some parallel verb structure? 
    # Without NLP, we rely on "parallel structure with comma + and/while/but".
    # We already checked 'compare' markers (while/but). 
    # If we have a comma and reasonable length, maybe? 
    # Spec: "two agents separated by comma... verbs on both sides"
    # Example: "Clients initiate requests, servers respond."
    if ',' in lower_text:
        # Check for balanced structure around comma
        parts = lower_text.split(',')
        if len(parts) == 2: # Limit to 2 parts for now
            # Heuristic: roughly equal complexity
            left_len = len(parts[0].split())
            right_len = len(parts[1].split())
            if left_len > 0 and right_len > 0:
                # Avoid "Hello, world" (2 words total)
                if left_len + right_len > 4:
                   return {
                       "diagram_worthy": True,
                       "diagram_kind": "compare",
                       "confidence": 0.6,
                       "reasons": ["Role differentiation (comma balance) detected"]
                   }
        pass 
        
    # Fallback / No signal
    return {
        "diagram_worthy": False,
        "diagram_kind": None,
        "confidence": 0.1,
        "reasons": ["No strong diagrammatic signal found."]
    }

def select_template(text: str) -> tuple[str | None, dict]:
    """
    Main entry point for decision making.
    Returns (diagram_kind, analysis_dict)
    """
    analysis = analyze_sentence(text)
    if analysis["diagram_worthy"]:
        return analysis["diagram_kind"], analysis
    return None, analysis
