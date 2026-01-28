from .utils import format_box, center_text

def template_priority(data: dict) -> list[str]:
    """
    Template A: Priority/Constraint
    Layout:
      [ Subject ]
           | Priority: ...
           v
      [ Focus ]
      ( Constraints... )
    """
    lines = []
    subject = data.get('subject', 'Unknown')
    focus = data.get('priority_target', 'Unknown')
    constraints = data.get('constraints', [])

    lines.extend(format_box(subject, width=20))
    lines.append(center_text("|", 20))
    lines.append(center_text("v", 20))
    lines.extend(format_box(focus, width=20))
    
    if constraints:
        c_text = ", ".join(constraints)
        if len(c_text) > 18:
            c_text = c_text[:15] + "..."
        lines.append(center_text(f"({c_text})", 20))
    
    return lines

def template_compare(data: dict) -> list[str]:
    """
    Template B: Compare
    Layout:
           [ Subject ]
           /         \\
      [ A ]           [ B ]
    """
    lines = []
    subject = data.get('subject', 'Unknown')
    targets = data.get('compare_targets', ['A', 'B'])
    
    lines.extend(format_box(subject, width=30))
    lines.append(center_text("/       \\", 30))
    
    # Left and Right boxes
    left = targets[0] if len(targets) > 0 else "?"
    right = targets[1] if len(targets) > 1 else "?"
    
    # Simple manual layout for now
    left_str = f"[{left[:8]}]"
    right_str = f"[{right[:8]}]"
    
    # Spacing
    gap = 7
    total_len = len(left_str) + gap + len(right_str)
    padding = (30 - total_len) // 2
    row = " " * padding + left_str + " " * gap + right_str
    lines.append(row)
    
    return lines

def template_category(data: dict) -> list[str]:
    """
    Template C: Category/Generic
    Layout:
      [ Subject ]
      : Info...
    """
    lines = []
    subject = data.get('subject', 'Unknown')
    action = data.get('action', '')
    
    lines.extend(format_box(subject, width=20))
    if action:
        lines.append(center_text(":", 20))
        lines.append(center_text(action, 20))
    
    return lines

