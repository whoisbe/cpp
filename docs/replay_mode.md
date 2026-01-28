# Replay Mode — behavior spec

Replay allows you to navigate a past run **offline**, with no LLM calls.

## CLI

One of:

- `cpp replay <run_path>`
- `cpp --replay <run_path>`

Choose what fits your CLI style; the behavior below must hold.

## Loading rules

Given `run_path` (a run folder):

- Load `run.json` (required)
- Load `ideas.json` (required)
- Load diagram files from `diagrams/` (optional)
  - If missing, treat all diagrams as `(none)`
- Validate that `len(ideas) == run.json["ideas_count"]`
  - If mismatch, still replay but show a debug warning (when `--debug`)

## Controls

- `[Enter]` next idea
- `[p]` previous idea
- `[q]` quit replay
- `[i]` show a short run summary (model names, created_at, ideas_count)

## Rendering

Must match live output format:

```
Idea <n>:
<idea sentence>

Diagram:
<diagram text or (none)>

[Enter] Next  [p] Prev  [q] Quit
```

## Flags in replay

- `--no-diagrams` hides diagrams even if they exist on disk.
- `--debug` prints whether a diagram existed and why it is hidden.
