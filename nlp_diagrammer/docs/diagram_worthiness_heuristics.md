# Diagram-worthiness Heuristics (v0)

Goal: Decide whether an idea sentence is *spatializable* (diagram-worthy) using conservative, deterministic heuristics.

This is a pre-check used by `nlp_diagrammer` to decide:
- which template to use, or
- to return `(none)`.

---

## Conceptual categories → heuristics

### 1) Compare / Trade-off (HIGH confidence)
**Signals**
- contains compare markers: `vs`, `versus`, `whereas`, `while`, `but`
- contains preference markers: `over`, `rather than`, `instead of`, `more than`, `less than`

**Diagram type**
- `compare`

**Example**
- “TCP prioritizes reliability over speed.”

---

### 2) Taxonomy / Categorization (HIGH)
**Signals**
- contains: `can be`, `either`, `or`, `types of`, `classified as`, `category`, `kinds of`
- patterns: `X are Y` where Y is plural category noun (best-effort)

**Diagram type**
- `category` (tree)

**Example**
- “Data can be structured, semi-structured, or unstructured.”

---

### 3) Part–whole / Composition (HIGH)
**Signals**
- contains: `consists of`, `includes`, `contains`, `made of`, `composed of`, `has`
- list-like punctuation: commas and `and` following these phrases

**Diagram type**
- `category` (parts tree)

**Example**
- “A request includes headers and a body.”

---

### 4) Properties / Constraints attached to an entity (MEDIUM–HIGH)
**Signals**
- property verbs: `ensures`, `provides`, `offers`, `supports`, `enforces`, `guarantees`
- constraint phrases:
  - `without <noun>`
  - `with <noun>`
  - `in <noun>` (use cautiously)
- adjective + noun phrase: e.g., “reliable delivery” (best-effort)

**Diagram type**
- `priority` (stacked properties)

**Example**
- “TCP ensures in-order delivery without loss.”

---

### 5) Role differentiation (MEDIUM)
**Signals**
- two agents separated by comma / conjunction:
  - “clients …, servers …”
- verbs on both sides (`initiate/respond`, `encode/decode`)
- parallel structure with comma + and/while/but

**Diagram type**
- `compare` (two columns)

**Example**
- “Clients initiate requests, servers respond.”

---

## Anti-signals (return none)
Apply after detecting a candidate category to avoid false positives.

### A) Pure assertions (LOW structure)
**Signals**
- sentence mostly adjectives + “is/are” with abstract nouns: “important”, “critical”, “matters”, “essential”
- no explicit second entity, no list, no constraints

### B) Idioms / slogans
**Signals**
- very short (<= 4 tokens) and contains common slogan patterns: “X first”, “less is more”, etc.
- (v0: keep a small denylist: `safety first`, `security first`)

### C) Mechanism-heavy (temporal/process)
**Signals**
- step words: `first`, `then`, `next`, `after`, `before`, `until`
- causal connectors: `because`, `so that`, `therefore`
- arrows implied by verbs: `sends`, `receives`, `retransmits` (use cautiously)

**Note:** These may be diagrammable later at a different altitude, but v0 should not.

---

## Output of the heuristic

Return a tuple:
- `diagram_worthy: bool`
- `diagram_kind: "compare" | "category" | "priority" | None`
- `confidence: 0.0..1.0`
- `reasons: list[str]`

---

## Suggested priority order

1. Compare / Trade-off
2. Part–whole
3. Taxonomy
4. Properties / Constraints
5. Role differentiation
6. Apply anti-signals (can downgrade to none)

---

## Notes for conservative implementation

- Prefer false negatives over false positives.
- If multiple kinds match, choose the one with highest confidence.
- If the chosen kind would require introducing new labels, return none.
