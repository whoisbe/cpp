# CPP v0 Stress Test (Domain-Agnostic Pacing + Diagram Humility)

Date: 2026-01-26

## Goal
Validate that the **Ideas + Diagram Humility** contract works across unrelated domains without:
- verbose flooding
- diagrams introducing new concepts
- domain-specific “canonical mappings”

## Test Method
For each prompt:
1) Generate 6–10 Ideas with optional diagrams (per upstream template).
2) Apply the proxy rule: reveal one Idea at a time.
3) Validate diagrams with the heuristic validator (hide on failure).

## Prompts (4 domains)

### 1) Audio / Sound Design
Prompt: “What’s the difference between harmonics and overtones in sound design?”

Expected:
- Ideas explain relationship without forcing numbering conventions.
- Diagrams are structural/relational; avoid invented ordinal labels unless present in Idea.

Acceptable:
Diagram:
Fundamental -> higher frequencies

Unacceptable:
Diagram:
1st harmonic (1st overtone)  # introduces ordinals not in Idea line

---

### 2) Physics
Prompt: “What’s the difference between fermions and bosons?”

Expected:
- Ideas focus on one contrast per item (statistics, exclusion, etc.).
- Diagrams should not introduce “spin”, “integer/half-integer” unless the Idea line says so.

Acceptable:
Diagram:
Particles
| fermions
| bosons

Unacceptable:
Diagram:
fermions -> half-integer spin  # adds “spin” if not in idea text

---

### 3) Networking
Prompt: “What’s the difference between TCP and UDP?”

Expected:
- Ideas cover reliability/ordering vs latency/overhead, one at a time.
- Diagrams should not add “handshake”, “three-way” unless stated in idea.

Acceptable:
Diagram:
Sender -> Receiver

Unacceptable:
Diagram:
SYN -> SYN-ACK -> ACK  # adds terms absent from idea text

---

### 4) ML Concepts
Prompt: “What’s the difference between supervised and unsupervised learning?”

Expected:
- Ideas contrast labeled vs unlabeled data; task names only if stated.
- Diagrams avoid adding algorithm names unless present in idea.

Acceptable:
Diagram:
Data -> model -> output

Unacceptable:
Diagram:
k-means  # if not in idea text

---

## Pass/Fail Criteria

### PASS if:
- Chunks are short, self-contained, and paced
- Diagrams are either:
  - consistent and minimal, or
  - omitted when risky
- Validator flags only genuinely overreaching diagrams

### FAIL if:
- LLM routinely produces diagrams that need “secret knowledge”
- Ideas depend on diagrams to be understood
- Validator hides most diagrams due to overly strict tokenization (tune STOPWORDS)

## Tuning Notes
If you see false positives from validator:
- add low-risk tokens to STOPWORDS (e.g., “input”, “output”)
- or relax `max_extras` to 1 for harmless tokens

Recommended v0 stance: **hide aggressively**; diagrams are optional.
