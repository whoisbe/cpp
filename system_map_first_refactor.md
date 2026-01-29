# CPP Refactor Proposal: “System Map First” (v0)

## Goal
Improve the experience for visual learners by generating **one overall concept map** for a batch of ideas, then presenting ideas one-by-one.

### New flow (high level)
1. Upstream question (user prompt)
2. LLM generates **N concise ideas**
3. LLM generates **ONE concept map** based on the N ideas (ASCII only)
4. Show the concept map first
5. Then enter the existing idea-by-idea loop (Next / Deeper / Switch angle)

---

## Architecture

### After (System Map First)
```
User Prompt
   |
Explainer LLM -> ideas[N]
   |
Map Visualizer LLM -> concept_map (ASCII)
   |
UI: show concept_map
   |
UI loop: show Idea 1..N (existing behavior)
```

---

## Separation of concerns
Still valid—just at a different granularity:

- **Explainer LLM:** produces ideas only
- **Map Visualizer LLM:** produces one system map from the list of ideas
- (Optional later) **Per-idea Visualizer:** micro-diagrams (today’s behavior)

---

## Map Visualizer prompt requirements
Input: numbered list of ideas.

Output:
- ASCII concept map ONLY (no prose)
- <= 18 lines (configurable)
- Prefer: hub/spoke, layered dependency maps, compare columns
- Avoid: step-by-step mechanism flowcharts
- Use idea numbers in node labels when possible

Example:
```
[1 Melody]     [2 Harmony]
      \          /
       \        /
        [6 Tonality]
             |
        [7 Intervals]
             |
   [3 Rhythm]   [4 Dynamics]
             \ /
            [5 Form]
```

---

## CLI UX
If `--map-first`:
1) Print:
   - “System Map”
   - map block
   - “Press Enter to start ideas…”
2) Wait for Enter
3) Start the usual idea loop

Optional helper flag for evaluation:
- `--no-idea-diagrams` to disable per-idea diagrams while testing map-first.

---

## Logging
In run folder:
- `concept_map.txt`

In `run.json` (top-level):
- `concept_map_generated: bool`
- `concept_map_prompt_version: "map_visualizer_v1"`
- `concept_map_model: <model>`

Replay:
- If `concept_map.txt` exists and the run indicates map-first, show it first. Otherwise unchanged.

---

## Minimal implementation steps
1. Add prompt: `prompts/map_visualizer_v1.md`
2. After ideas generation, call map visualizer when `--map-first`
3. Save and print map before idea loop
4. Add logging fields + replay support
