"""CLI interface for Conversational Pacing Proxy."""

from __future__ import annotations

import sys
from typing import Any, Dict, Optional

from .llm import LLMClient
from .proxy import ConversationProxy


def format_chunk(chunk: Dict[str, Any], index: int, debug: bool = False) -> str:
    """Format a chunk for display.

    Always includes a Diagram block: either the diagram or "Diagram: (none)".
    When debug=True and chunk has _debug, appends validator decision (hidden/shown + extra tokens).

    Args:
        chunk: Dict with 'idea', optional 'diagram', and optional '_debug'.
        index: Zero-based index of the chunk.
        debug: Whether to append debug info when available.

    Returns:
        Formatted string with idea, diagram block, and optional debug line.
    """
    lines = [f"Idea {index + 1}:"]
    lines.append(chunk["idea"])
    lines.append("")  # Blank line before Diagram block

    if chunk.get("diagram"):
        lines.append("Diagram:")
        lines.append(chunk["diagram"])
    else:
        lines.append("Diagram: (none)")

    if debug and "_debug" in chunk:
        d = chunk["_debug"]
        hidden = d.get("hidden", False)
        extra = d.get("extra_tokens", ())
        if hidden:
            tok = f" (extra tokens: {', '.join(extra)})" if extra else ""
            lines.append(f"  [debug] diagram hidden{tok}")
        else:
            lines.append("  [debug] diagram shown")

    return "\n".join(lines) + "\n"


def display_controls(has_next: bool) -> str:
    """Display control options."""
    controls = []
    if has_next:
        controls.append("[Enter] Next")
    controls.append("[d] Deeper")
    controls.append("[s] Switch angle")
    controls.append("[q] Quit")
    return "  ".join(controls)


def run_interactive_loop(proxy: ConversationProxy) -> None:
    """Run the interactive conversation loop."""
    while True:
        chunk = proxy.get_current_chunk()

        if chunk is None:
            print("\nNo more ideas available.")
            break

        print(f"\n{format_chunk(chunk, proxy.current_index, debug=proxy.debug)}")
        print(display_controls(proxy.has_next()))

        try:
            user_input = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if user_input == "" or user_input == "next":
            if not proxy.next():
                print("\nNo more ideas available.")
                break
        elif user_input == "d":
            proxy.go_deeper()
            print("(Deeper functionality not implemented in v0)")
        elif user_input == "s":
            proxy.switch_angle()
            print("(Switch angle functionality not implemented in v0)")
        elif user_input == "q":
            print("\nGoodbye!")
            break
        else:
            print("Invalid input. Use: enter/next, d, s, or q")


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Conversational Pacing Proxy - Human-like conversational pacing for LLMs"
    )
    parser.add_argument("command", choices=["ask"], help="Command to execute")
    parser.add_argument("prompt", help="User prompt or question")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Upstream LLM model identifier (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (defaults to OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Always hide diagrams, even if present in upstream output",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print validator decisions: extra tokens and whether diagram was hidden",
    )

    args = parser.parse_args()

    if args.command == "ask":
        try:
            llm_client = LLMClient(model=args.model, api_key=args.api_key)
            proxy = ConversationProxy(
                llm_client,
                no_diagrams=args.no_diagrams,
                debug=args.debug,
            )
            print(f"Processing: {args.prompt}\n")
            proxy.start_conversation(args.prompt)
            run_interactive_loop(proxy)
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
