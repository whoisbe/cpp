# Conversational Pacing Proxy (CPP)

A lightweight proxy layer between a user and an LLM that enforces **human-like conversational pacing**. The proxy prioritizes *progressive disclosure*, *brevity*, and *curiosity-by-constraint* rather than raw completeness.

## Installation

```bash
pip install -e .
```

## Setup

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your-api-key-here
```

## Usage

```bash
cpp ask "What is context engineering?"
```

The CLI will:
1. Make one upstream LLM call
2. Parse the response into chunks
3. Display one chunk at a time
4. Present control options after each chunk

### Controls

- `enter` or `next` → Show next chunk
- `d` → Go deeper on current chunk (placeholder in v0)
- `s` → Switch angle (placeholder in v0)
- `q` → Quit session

## Example

```
> cpp ask "What is context engineering?"

Processing: What is context engineering?

Idea 1:
Context engineering shapes how a model responds by carefully designing prompts, roles, and constraints.

[next] Continue  [d] Deeper  [s] Switch angle  [q] Quit

> 
```

## Development

This is a minimal MVP implementation following the spec in `docs/spec.md`.
