# CPP — Shadow NLP Diagram Logging (Spec)

## Goal
For each Idea in a run, compute an **NLP Diagrammer** diagram and analysis **regardless** of the LLM diagram outcome.

- This is **not** shown to the user (v0).
- This is stored in run artifacts to build a dataset for later evaluation/ML.

## Where it runs
During `cpp ask` runtime, after each idea is produced (or when it is displayed, depending on your existing flow), run:

- `nlp_diagrammer.render_diagram(idea_text)` (may return None)
- `nlp_diagrammer.heuristics.analyze_sentence(idea_text)` (returns analysis)

## Output artifacts

### 1) run.json (schema extension)
Add a nested object per item:

```json
{
  "index": 1,
  "idea_text": "...",
  "diagram_generated": true,
  "diagram_hidden": false,
  "hidden_reason": null,
  "extra_tokens": [],
  "nlp": {
    "attempted": true,
    "diagram": "TCP\n |\nPriority: reliability\n",
    "diagram_kind": "priority",
    "confidence": 0.82,
    "reasons": ["priority_verb", "tradeoff_over"]
  }
}
```

Rules:
- `nlp.attempted` is true when NLP diagrammer code executed for this idea.
- `nlp.diagram` is a **single string** exactly as stored (including newlines) OR null when no diagram.
- `nlp.diagram_kind` is null if not diagram-worthy or unknown.
- `nlp.confidence` is null if not produced.
- `nlp.reasons` is an array (can be empty).

### 2) Additional files (optional but recommended)
In the run folder, add:

```
nlp_diagrams/
  001.txt
  002.txt
  ...
```

Where each file contains either:
- the diagram text (no wrapper) OR
- `(none)`

This mirrors `diagrams/` for LLM output and makes diffing easy.

## Feature flags
Add CLI flag:
- `--nlp-shadow` (default: ON for now is acceptable if overhead is negligible; otherwise default OFF)

If disabled:
- do not attempt NLP diagrammer
- do not add nlp fields (or set `attempted=false` consistently)

Recommendation: keep it ON by default for the dataset value, but allow OFF for purity.

## Versioning
If you want strict schema versioning, bump:
- `run.json.version` from 1 -> 2
and keep backward compatibility in replay:
- ignore unknown fields
- if version=1, treat missing `nlp` as not attempted

## Replay behavior
Replay should ignore `nlp` fields for display (v0). No UI changes.

## Data integrity
- Ensure `len(ideas.json)` matches `items` length.
- Ensure `nlp_diagrams/NNN.txt` count matches ideas_count when enabled.
