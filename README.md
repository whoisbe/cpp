# Conversational Pacing Proxy (CPP)

A lightweight proxy layer between a user and an LLM that enforces **human-like conversational pacing**. The proxy prioritizes *progressive disclosure*, *brevity*, and *curiosity-by-constraint* rather than raw completeness.

## Overview

Modern LLMs optimize for completeness and helpfulness, often producing responses that are verbose, front-loaded with information, and poorly paced for human conversation. CPP addresses this by delivering high-quality content *one spoon at a time*, mimicking how two thoughtful humans converse.

## Features

- **Progressive Disclosure**: Reveals information one conceptual unit at a time
- **User Agency**: User controls the pace and direction of the conversation
- **Brevity-First**: Prioritizes concise, digestible chunks over comprehensive dumps
- **Optional Diagrams**: Per-idea ASCII diagrams, validated against the idea text (hidden if they introduce new terms)
- **Interactive CLI**: Simple command-line interface with intuitive controls

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cpp
```

2. Install the package:
```bash
pip install -e .
```

Note: This project uses a uv workspace that includes `nlp_diagrammer` as a sibling package. The workspace is configured in `pyproject.toml`. If imports fail, ensure `nlp_diagrammer` is available in the workspace or adjust the import path in `cpp/nlp_import.py`.

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-api-key-here
```

## Usage

### Basic Usage

```bash
cpp ask "What is context engineering?"
```

Or run via module:

```bash
python -m cpp.cli ask "What is context engineering?"
```

The CLI will:
1. Make one upstream LLM call
2. Parse the response into chunks
3. Display one chunk at a time
4. Present control options after each chunk

### CLI Options

- **`--no-diagrams`** — Always hide diagrams, even if the upstream model includes them.
- **`--debug`** — Print validator decisions for each chunk: extra tokens (if any) and whether the diagram was shown or hidden.
- **`--no-nlp-shadow`** — Disable shadow NLP diagram logging (default: enabled). When enabled, NLP-based diagram analysis is computed and logged alongside LLM diagrams for comparison.

Example:

```bash
python -m cpp.cli ask "what's the difference between harmonics and overtones?" --debug
```

Diagrams are **optional** and **validated** against the idea text. A diagram is shown only if it reuses terms from the idea; otherwise it is replaced with `Diagram: (none)`. Use `--debug` to see which diagrams were accepted or hidden.

### Controls

- **Enter** or `next` → Show next chunk
- `d` → Go deeper on current chunk (placeholder in v0)
- `s` → Switch angle (placeholder in v0)
- `q` → Quit session

### Example Session

```
> cpp ask "What is context engineering?"

Processing: What is context engineering?

Idea 1:
Context engineering shapes how a model responds by carefully designing prompts, roles, and constraints.

Diagram: (none)

[Enter] Next  [d] Deeper  [s] Switch angle  [q] Quit

> 
```

## Architecture

The system consists of three main components:

- **CLI (`cpp/cli.py`)**: Handles user interaction and input/output
- **Proxy (`cpp/proxy.py`)**: Manages conversation pacing and chunking
- **LLM (`cpp/llm.py`)**: Interfaces with the OpenAI API

See `docs/spec.md` for detailed architecture and design decisions.

## Stress Testing

Run automated stress tests:

```bash
python scripts/run_stress.py
```

Or using make:

```bash
make stress
```

This runs a suite of prompts and generates summary reports in `runs_stress/_reports_<timestamp>/`. See `docs/stress_automation.md` for details.

## Development

This is a minimal MVP implementation following the spec in `docs/spec.md`.

### Project Structure

```
cpp/
├── cpp/
│   ├── __init__.py
│   ├── cli.py             # Command-line interface
│   ├── diagram_validator.py  # Diagram humility validation
│   ├── llm.py             # LLM integration
│   ├── parser.py          # Upstream response parsing
│   ├── prompts/           # Upstream prompt template
│   └── proxy.py           # Pacing proxy logic
├── docs/
│   ├── spec.md            # Detailed specification
│   └── sequence-diagram.md
├── pyproject.toml         # Project configuration
├── requirements.txt       # Python dependencies
└── README.md
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines if applicable]
