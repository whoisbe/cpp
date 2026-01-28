import re
from .templates import template_priority, template_compare, template_category
from .utils import clean_text
from .heuristics import (
    select_template, 
    COMPARE_MARKERS, 
    PREFERENCE_MARKERS, 
    PRIORITY_VERBS,
    PROPERTY_VERBS
)

# Combine markers for extraction
ALL_COMPARE = COMPARE_MARKERS | PREFERENCE_MARKERS
ALL_PRIORITY = PRIORITY_VERBS | PROPERTY_VERBS

def extract_info(idea_text: str, template_type: str = 'category') -> dict:
    """
    Heuristic extraction of semantic components.
    """
    text = clean_text(idea_text)
    words = text.split()
    lower_words = [w.lower().rstrip('.,:;') for w in words]
    
    # Identify Template Type (Now passed in or determined externally, but keeping fallback logic for extraction if needed)
    # We rely on the passed 'template_type' now.
        
    info = {
        'subject': 'Unknown',
        'template_type': template_type,
        'action': '',
        'constraints': []
    }
    
    # Heuristic: Find the main verb/pivot
    pivot_idx = -1
    pivot_word = ''
    
    if template_type == 'compare':
        for i, w in enumerate(lower_words):
            if w in ALL_COMPARE:
                pivot_idx = i
                pivot_word = words[i]
                break
    elif template_type == 'priority':
        for i, w in enumerate(lower_words):
            if w in ALL_PRIORITY:
                pivot_idx = i
                pivot_word = words[i]
                break
    
    # Subject Extraction
    if pivot_idx > 0:
        # Improved Subject Logic:
        # If there is a verb before the main pivot, split there.
        verb_idx = -1
        for i in range(pivot_idx):
             if lower_words[i] in ALL_PRIORITY: 
                 verb_idx = i
                 break
        
        if verb_idx > -1 and template_type == 'compare':
             info['subject'] = " ".join(words[:verb_idx])
             info['compare_targets'] = [
                 " ".join(words[verb_idx+1:pivot_idx]),
                 " ".join(words[pivot_idx+1:])
             ]
        else:
             info['subject'] = " ".join(words[:pivot_idx])
             if template_type == 'priority':
                 info['priority_target'] = " ".join(words[pivot_idx+1:])
             elif template_type == 'compare':
                 lhs = words[:pivot_idx]
                 rhs = words[pivot_idx+1:]
                 info['subject'] = clean_text(" ".join(lhs))
                 info['compare_targets'] = [clean_text(" ".join(lhs)), clean_text(" ".join(rhs))]
                 
    else:
        # Category / Fallback
        info['subject'] = words[0] if words else "Unknown"
        info['action'] = " ".join(words[1:]) if len(words) > 1 else ""

    # Constraint Extraction (Global check)
    without_matches = re.split(r'\bwithout\b', text, flags=re.IGNORECASE)
    if len(without_matches) > 1:
        constraint_part = without_matches[1].strip()
        width_match = re.match(r'^([^.,:;]+)', constraint_part)
        if width_match:
            info['constraints'].append(f"No {width_match.group(1)}")
            if 'priority_target' in info:
                info['priority_target'] = info['priority_target'].split('without')[0].strip()

    return info


def explain_parse(idea_text: str) -> dict:
    """
    Return debugging info about how the text is parsed.
    """
    return extract_info(idea_text)

def render_diagram(idea_text: str) -> list[str] | None:
    """
    Main entry point: text -> ASCII lines.
    """
    kind, _ = select_template(idea_text)
    if not kind:
        return None

    info = extract_info(idea_text, template_type=kind)
    
    if info['template_type'] == 'priority':
        return template_priority(info)
    elif info['template_type'] == 'compare':
        return template_compare(info)
    else:
        return template_category(info)
