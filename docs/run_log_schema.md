# Run Log Schema (run.json) — version 1

A **run** is created for each `cpp ask ...` invocation when logging is enabled.

## Folder layout

```
runs/
  YYYY-MM-DD_HHMMSS_slug/
    run.json
    explain.txt
    ideas.json
    diagrams/
      001.txt
      002.txt
      ...
```

## run.json (version 1)

```json
{
  "version": 1,
  "created_at": "2026-01-27T16:34:55-05:00",
  "user_prompt": "What's the difference between TCP and UDP?",
  "explainer": {
    "model": "…",
    "prompt_file": "prompts/explainer_v1.md",
    "prompt_sha256": "…"
  },
  "visualizer": {
    "model": "…",
    "prompt_file": "prompts/visualizer_v1.md",
    "prompt_sha256": "…"
  },
  "diagram_policy": "eager",
  "validator": {
    "enabled": true,
    "max_extras": 0
  },
  "ideas_count": 10,
  "items": [
    {
      "index": 1,
      "idea_text": "TCP is a connection-oriented protocol that ensures reliable data transmission between sender and receiver.",
      "diagram_generated": true,
      "diagram_hidden": false,
      "hidden_reason": null,
      "extra_tokens": []
    }
  ]
}
```

### Field notes

- `index` is **1-based** and matches the diagrams filenames (`001.txt` => index 1).
- `diagram_generated` is **true** if the visualizer produced something other than `(none)` **before** local hiding.
- `diagram_hidden` is **true** if the proxy ultimately hides the diagram due to validation or flags.
- `hidden_reason` values (suggested):
  - `validator_extra_tokens`
  - `flag_no_diagrams`
- `extra_tokens` is the list of tokens that triggered hiding (when applicable).

## ideas.json

A JSON array of idea sentence strings (no `Idea n:` prefix), length must equal `ideas_count`.

## diagrams/NNN.txt

The final diagram as shown to the user (after validation/flags) OR `(none)`.
