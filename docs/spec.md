# Conversational Pacing Proxy (CPP)

## Status

Revised Draft v0 — personal-use MVP

## Purpose

Build a lightweight proxy layer between a user and an LLM that enforces **human-like conversational pacing**. The proxy prioritizes *progressive disclosure*, *brevity*, and *curiosity-by-constraint* rather than raw completeness.

The system is designed first for **personal daily use** and secondarily for potential generalization into a shippable product.

---

## Problem Statement

Modern LLMs optimize for completeness and helpfulness, often producing responses that are:

* Verbose
* Front-loaded with information
* Poorly paced for human conversation

This leads to cognitive overload and breaks the illusion of natural dialogue.

**Goal:** Deliver the same high-quality content *one spoon at a time*, mimicking how two thoughtful humans converse.

---

## Non-Goals (v0)

* No attempt to improve factual accuracy or reasoning quality
* No long-term memory or personalization
* No multi-agent orchestration
* No emotional coaching or therapeutic behavior
* No UI polish beyond functional CLI interaction
* No domain-specific knowledge injection or canonical mappings

---

## Core Principles

1. **Pacing over intelligence**
   The proxy controls *when* and *how much* information is revealed, not *what* is true.

2. **Progressive disclosure**
   Never reveal more than one conceptual unit at a time.

3. **User agency**
   The user always decides whether to continue, deepen, or redirect.

4. **Curiosity via constraint**
   Curiosity emerges by stopping early and offering choices — not by forced Socratic questioning.

5. **Determinism first, LLM second**
   Prefer predictable logic; use additional LLM calls only if necessary.

6. **Text is the source of truth**
   Visuals (diagrams) are derived artifacts and must never introduce new concepts.

---

## High-Level Architecture

```
User
  ↓
CLI Interface
  ↓
Conversation Controller (Proxy)
  ↓
Upstream LLM (single call)
```

The proxy:

* Requests a structured response from the LLM
* Stores the full response internally
* Reveals content incrementally based on user input

---

## Conversation Contract (v0)

### Turn Rules

* Max **1 chunk per assistant turn**
* Each chunk:

  * expresses exactly **one idea**
  * ≤ **30 words** (soft limit)
* Each turn ends with **control**, not explanation

---

## Diagram-per-Idea Contract (Revised)

Diagrams are **optional grounding aids**, not explanations.

### Diagram Rules

* Each chunk **may include** a `Diagram:` block
* Diagrams are **ASCII-only** and optional
* Diagrams must visually reinforce the idea *without adding new knowledge*

### Strict Constraints

* Diagrams may **only reuse terms or phrases that appear verbatim in the Idea text**
* Diagrams must **not introduce new labels, numbering systems, or distinctions**
* If the idea involves definitions, terminology, or naming conventions, diagrams must be:

  * structural
  * relational
  * or abstract
* Ordinal numbers, formal labels, or technical symbols are **disallowed unless explicitly present in the idea text**

### Diagram Size & Style

* ≤ **8 lines** total
* Simple characters only: `-|/\\<>[]()_`

### Allowed Diagram Archetypes

* **Flow** (process or progression)
* **Loop** (cyclical relationship)
* **Tree** (categorical split)
* **Compare** (side-by-side contrast, ≤ 3 rows)

### Diagram Fallback

* If a meaningful diagram cannot be produced under these constraints, output:

  * `Diagram: (none)`

---

## Upstream LLM Prompt Specification

The upstream LLM is instructed to produce **structured, chunkable output** with diagram humility.

Example system instruction:

> Answer the user’s question using 6–10 short, self-contained ideas.
>
> For each idea, output in the following format:
>
> Idea: one sentence expressing exactly one idea (≤ 30 words)
> Diagram: an optional ASCII diagram that reuses only words or phrases from the Idea text, or `(none)` if not applicable
>
> Rules:
>
> * Each idea must stand on its own
> * Do not introduce new terminology in diagrams
> * Prefer structural or relational diagrams over labeled or numbered ones
> * If unsure, omit the diagram
> * Do not include summaries or conclusions

This prompt intentionally biases toward **clarity, humility, and pacing**.

---

## Proxy Responsibilities

### Required

* Issue exactly **one upstream LLM call** per user prompt
* Parse response into an ordered list of chunks
* Store full chunk list in session state
* Track current chunk index
* Display exactly one chunk at a time
* Present user with explicit next-action choices

### Optional (v0.1+)

* Diagram validation (hide diagram if it introduces new terms)
* Diagram repair via scoped second-pass LLM call
* Debug mode to surface raw upstream output

---

## CLI Interaction Flow

### Initial Prompt

```
> cpp ask "What is context engineering?"
```

### Example Output

```
Idea 1:
Context engineering shapes how a model responds by carefully designing prompts, roles, and constraints.

Diagram:
Prompt -> Model -> Response

[next] Continue  [d] Deeper  [s] Switch angle  [q] Quit
```

---

## Session State (In-Memory)

* user_prompt: string
* chunks: list[string]
* current_index: int
* upstream_model: identifier

Persistence is explicitly out of scope.

---

## Success Criteria

The MVP is successful if, after repeated use:

1. The user experiences **less cognitive overload**
2. The user interrupts the model **less often**
3. The interaction feels **closer to human turn-taking**

If these are not met, the concept should be revisited before adding features.

---

## Future Directions (Explicitly Deferred)

* Web UI with progressive reveal cards
* Per-user pacing profiles
* Adaptive curiosity layer
* Diagram format toggles (ASCII / Mermaid)
* Memory and personalization

---

## Guiding Question

> “Does this feel like someone who knows when to stop talking?”

If yes, the proxy is doing its job.
