## Summary of Changes

### 1. **Prompts loader** (`cpp/prompts/`)
- **`cpp/prompts/__init__.py`** – New package, exports `load_upstream_prompt`.
- **`cpp/prompts/loader.py`** – Loads `upstream_prompt_template.md` via `importlib.resources.read_text("cpp.prompts", ...)`, falls back to repo-root `./prompts/` when running from source. Replaces `{{USER_PROMPT}}` with the user query.
- **`cpp/prompts/upstream_prompt_template.md`** – Copy of `./prompts/upstream_prompt_template.md` (same content) so it’s usable as a package resource.

### 2. **Parser** (`cpp/parser.py`)
- **`Chunk`** dataclass: `index`, `idea_text`, `diagram_lines` (optional `List[str]` or `None`).
- **`parse_chunks(raw)`** – Splits on `Idea <n>:`, then finds `Diagram:` (after newline or space). Diagram runs until a blank line. `Diagram: (none)` → `diagram_lines is None`. Returns `List[Chunk]`.

### 3. **Diagram validation** (`cpp/diagram_validator.py`)
- **`_run_mini_tests()`** – Two cases:
  1. Diagram introduces `"1st"` when it’s not in the idea → `validate_diagram` fails, `should_hide_diagram` True.
  2. Diagram only reuses idea tokens → `validate_diagram` passes, `should_hide_diagram` False.
- Run with: `python -m cpp.diagram_validator`.

### 4. **LLM** (`cpp/llm.py`)
- **`generate_raw(system_prompt)`** – Single upstream call with `system_prompt` as system message and `"Proceed."` as user message. Returns raw response text. All parsing/validation removed.

### 5. **Proxy** (`cpp/proxy.py`)
- **`__init__(llm_client, no_diagrams=False, debug=False)`** – New flags.
- **`start_conversation(user_prompt)`** – Loads template via `load_upstream_prompt`, calls `llm.generate_raw`, parses with `parse_chunks`, then `_resolve_chunks`:
  - For each chunk with `diagram_lines`: `validate_diagram(idea_text, diagram_lines)` → `should_hide_diagram`. If hide (or `no_diagrams`), set `diagram` to `None`.
  - Stores `{idea, diagram, _debug?}`. `_debug` includes `hidden`, `reason`, `extra_tokens` when `debug=True`.

### 6. **CLI** (`cpp/cli.py`)
- **`--no-diagrams`** – Always hide diagrams.
- **`--debug`** – Print validator outcome per chunk (extra tokens + hidden/shown).
- **`format_chunk(chunk, index, debug)`** – Always emits a `Diagram:` block: either the diagram or `Diagram: (none)`. With `debug` and `_debug`, appends e.g. `[debug] diagram hidden (extra tokens: 1st)` or `[debug] diagram shown`.
- **`display_controls`** – Uses `[Enter] Next` when there is a next chunk; Enter / `next` still advance.
- Proxy is constructed with `no_diagrams=args.no_diagrams`, `debug=args.debug`.

### 7. **Build** (`pyproject.toml`)
- `packages = ["cpp", "cpp.prompts"]`, `cpp.prompts = ["*.md"]` so the template is installed as package data.

### 8. **README**
- Features: optional diagrams, validated against idea text.
- New “CLI options”: `--no-diagrams`, `--debug`, and example `python -m cpp.cli ask "..." --debug`.
- Short note on diagram validation and `Diagram: (none)`.
- Example session shows `Diagram: (none)` and `[Enter] Next`.
- Project layout updated to include `diagram_validator`, `parser`, `prompts/`.

---

## Assumptions

1. **Prompt source** – Template is loaded from `cpp.prompts` (package resource). Repo-root `./prompts/` is used only as fallback when running from source. `./prompts/upstream_prompt_template.md` remains the editable source; `cpp/prompts/upstream_prompt_template.md` is a bundled copy.
2. **Parser format** – `Idea <n>: ...` with `n` numeric. `Diagram:` can follow a newline or a space (same line). Diagram ends at first blank line. `Diagram: (none)` means no diagram.
3. **Validation** – `validate_diagram(idea_line, diagram_lines)` and `should_hide_diagram(result)` are used as defined in `diagram_validator`. Hiding = treating as no diagram and showing `Diagram: (none)`.
4. **No extra LLM calls** – Validation is local only; no second pass.
5. **CLI** – Run as `python -m cpp.cli ask "..."` because `cpp` often clashes with the C compiler. README shows both `cpp ask` and `python -m cpp.cli ask`.
6. **Controls** – Existing behavior kept: Enter / `next` → next chunk, `q` → quit, `d` / `s` still placeholders.

---

## How to verify

```bash
# Validator tests
python -m cpp.diagram_validator

# Parser + loader
python -c "from cpp.parser import parse_chunks; from cpp.prompts import load_upstream_prompt; print(load_upstream_prompt('x')[:60]); print(parse_chunks('Idea 1: a\nDiagram: (none)'))"

# CLI flags
python -m cpp.cli ask --help

# E2E (requires OPENAI_API_KEY)
python -m cpp.cli ask "what's the difference between harmonics and overtones?" --debug
```

With `--debug`, you get per-chunk validator decisions (extra tokens + hidden/shown). With `--no-diagrams`, all diagrams are hidden and you only see `Diagram: (none)`.