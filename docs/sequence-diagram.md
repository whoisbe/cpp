# CPP Sequence Diagram

Mermaid sequence diagram showing how the **Conversational Pacing Proxy (CPP)** works from CLI invocation through the interactive loop.

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant CLI
    participant Proxy as ConversationProxy
    participant LLM as LLMClient
    participant OpenAI as Upstream LLM (OpenAI)

    %% --- Initialization & single upstream call ---
    User->>CLI: cpp ask "What is context engineering?" [--model] [--api-key]
    CLI->>CLI: Parse args (command, prompt, model, api-key)
    CLI->>LLM: new LLMClient(model, api_key)
    CLI->>Proxy: new ConversationProxy(llm_client)
    CLI->>User: "Processing: {prompt}"
    CLI->>Proxy: start_conversation(prompt)

    Proxy->>Proxy: Store user_prompt, set current_index = 0
    Proxy->>LLM: generate_chunks(user_prompt)

    LLM->>LLM: Build system prompt (6–10 ideas, Idea:/Diagram format)
    LLM->>OpenAI: chat.completions.create(system + user message)
    OpenAI-->>LLM: Raw response text
    LLM->>LLM: _parse_structured_chunks(content)
    LLM->>LLM: For each Idea: block → validate diagram, build chunk dict
    LLM-->>Proxy: List of chunks [{idea, diagram?}, ...]

    Proxy->>Proxy: Store chunks, current_index = 0

    %% --- Interactive loop ---
    loop run_interactive_loop
        CLI->>Proxy: get_current_chunk()
        Proxy-->>CLI: chunk or None

        alt No chunk
            CLI->>User: "No more ideas available." / exit loop
        else Has chunk
            CLI->>CLI: format_chunk(chunk, index) → "Idea N:" + idea + diagram
            CLI->>User: Display idea + optional diagram
            CLI->>Proxy: has_next()
            Proxy-->>CLI: true / false
            CLI->>User: "[next] Continue  [d] Deeper  [s] Switch angle  [q] Quit"
            CLI->>User: "> "
            User->>CLI: input (enter/next | d | s | q)

            alt enter or "next"
                CLI->>Proxy: next()
                Proxy->>Proxy: current_index += 1 if has_next
                Proxy-->>CLI: true / false
                Note over CLI: If false → "No more ideas", break
            else "d" (deeper)
                CLI->>Proxy: go_deeper()
                Note over Proxy: v0 placeholder — no-op
                CLI->>User: "(Deeper functionality not implemented in v0)"
            else "s" (switch angle)
                CLI->>Proxy: switch_angle()
                Note over Proxy: v0 placeholder — no-op
                CLI->>User: "(Switch angle functionality not implemented in v0)"
            else "q" (quit)
                CLI->>User: "Goodbye!"
                CLI->>CLI: break loop
            else invalid
                CLI->>User: "Invalid input. Use: enter/next, d, s, or q"
            end
        end
    end
```

## Legend

| Actor | Role |
|-------|------|
| **User** | Runs `cpp ask "…"` and interacts via prompts |
| **CLI** | `cli.py`: argparse, `run_interactive_loop`, formatting, I/O |
| **ConversationProxy** | `proxy.py`: session state, chunk storage, `next` / `go_deeper` / `switch_angle` |
| **LLMClient** | `llm.py`: system prompt, single OpenAI call, parse Idea:/Diagram → chunks |
| **Upstream LLM** | OpenAI API; returns structured text, proxy does not stream |

## Design notes

- **Exactly one** upstream LLM call per user prompt (`start_conversation` → `generate_chunks`).
- Proxy stores the full chunk list and reveals **one chunk per turn**; `next()` just advances `current_index`.
- Controls (`[next]`, `[d]`, `[s]`, `[q]`) are shown every turn; `d` and `s` are placeholders in v0.
