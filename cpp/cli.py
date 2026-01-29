"""CLI interface for Conversational Pacing Proxy."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .llm import LLMClient
from .proxy import ConversationProxy
from .run_logger import load_run_metadata, load_ideas, load_diagram, load_concept_map


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
            reason = d.get("reason", "")
            if reason:
                lines.append(f"  [debug] diagram hidden ({reason}){tok}")
            else:
                lines.append(f"  [debug] diagram hidden{tok}")
        else:
            existed = chunk.get("diagram") is not None
            if existed:
                lines.append("  [debug] diagram shown")
            else:
                lines.append("  [debug] diagram not generated")

    return "\n".join(lines) + "\n"


def display_controls(has_next: bool, has_prev: bool = False, is_replay: bool = False) -> str:
    """Display control options."""
    controls = []
    if has_next:
        controls.append("[Enter] Next")
    if has_prev:
        controls.append("[p] Prev")
    if is_replay:
        controls.append("[i] Info")
    controls.append("[q] Quit")
    return "  ".join(controls)


def run_interactive_loop(proxy: ConversationProxy, is_replay: bool = False) -> None:
    """Run the interactive conversation loop."""
    while True:
        chunk = proxy.get_current_chunk()

        if chunk is None:
            print("\nNo more ideas available.")
            break

        has_prev = proxy.current_index > 0
        print(f"\n{format_chunk(chunk, proxy.current_index, debug=proxy.debug)}")
        print(display_controls(proxy.has_next(), has_prev=has_prev, is_replay=is_replay))

        try:
            user_input = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if user_input == "" or user_input == "next":
            if not proxy.next():
                print("\nNo more ideas available.")
                break
        elif user_input == "p" or user_input == "prev":
            if not proxy.previous():
                print("\nAlready at first idea.")
        elif user_input == "i" or user_input == "info":
            if is_replay:
                _show_replay_info(proxy)
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
            print("Invalid input. Use: enter/next, p/prev, i/info (replay), d, s, or q")


def _show_replay_info(proxy: ConversationProxy) -> None:
    """Show run metadata summary in replay mode."""
    if not hasattr(proxy, 'run_metadata'):
        return
    
    meta = proxy.run_metadata
    print("\n--- Run Summary ---")
    print(f"Created: {meta.get('created_at', 'unknown')}")
    print(f"User prompt: {meta.get('user_prompt', 'unknown')}")
    print(f"Explainer model: {meta.get('explainer', {}).get('model', 'unknown')}")
    print(f"Visualizer model: {meta.get('visualizer', {}).get('model', 'unknown')}")
    print(f"Ideas count: {meta.get('ideas_count', 0)}")
    print("------------------\n")


class ReplayProxy:
    """Proxy for replay mode that loads from disk."""
    
    def __init__(
        self,
        run_path: Path,
        *,
        no_diagrams: bool = False,
        debug: bool = False,
    ):
        """Initialize replay proxy.
        
        Args:
            run_path: Path to run directory.
            no_diagrams: If True, hide diagrams even if present.
            debug: If True, show debug info.
        """
        self.run_path = run_path
        self.no_diagrams = no_diagrams
        self.debug = debug
        self.run_metadata = load_run_metadata(run_path)
        self.ideas = load_ideas(run_path)
        self.current_index = 0
        
        # Load concept map if it exists and run indicates map-first mode
        self.concept_map_text: Optional[str] = None
        if self.run_metadata.get("concept_map_generated", False):
            self.concept_map_text = load_concept_map(run_path)
        
        # Validate ideas count
        expected_count = self.run_metadata.get("ideas_count", 0)
        if len(self.ideas) != expected_count and debug:
            print(f"[debug] Warning: ideas.json has {len(self.ideas)} ideas, "
                  f"but run.json says {expected_count}", file=sys.stderr)
    
    def get_current_chunk(self) -> Optional[Dict[str, Any]]:
        """Return the current chunk to display."""
        if self.current_index >= len(self.ideas):
            return None
        
        idea_text = self.ideas[self.current_index]
        
        # Load diagram from disk
        diagram: Optional[str] = None
        diagram_existed = False
        hidden_reason: Optional[str] = None
        
        if not self.no_diagrams:
            diagram_text = load_diagram(self.run_path, self.current_index + 1)
            if diagram_text and diagram_text != "(none)":
                diagram_existed = True
                diagram = diagram_text
            elif diagram_text == "(none)":
                diagram_existed = False
        else:
            # Check if diagram exists even if we're hiding it
            diagram_text = load_diagram(self.run_path, self.current_index + 1)
            if diagram_text and diagram_text != "(none)":
                diagram_existed = True
                hidden_reason = "flag_no_diagrams"
        
        chunk: Dict[str, Any] = {"idea": idea_text, "diagram": diagram}
        
        if self.debug:
            # Get metadata from run.json if available
            items = self.run_metadata.get("items", [])
            item_meta = None
            if self.current_index < len(items):
                item_meta = items[self.current_index]
            
            debug_info = {
                "hidden": hidden_reason is not None or (item_meta and item_meta.get("diagram_hidden", False)),
                "reason": hidden_reason or (item_meta and item_meta.get("hidden_reason")),
                "extra_tokens": tuple(item_meta.get("extra_tokens", []) if item_meta else []),
            }
            if not diagram_existed and not hidden_reason:
                debug_info["reason"] = "not_generated"
            chunk["_debug"] = debug_info
        
        return chunk
    
    def has_next(self) -> bool:
        """Return True if there are more ideas after the current one."""
        return self.current_index < len(self.ideas) - 1
    
    def next(self) -> bool:
        """Advance to the next idea. Return True if advanced, False if at end."""
        if self.has_next():
            self.current_index += 1
            return True
        return False
    
    def previous(self) -> bool:
        """Go back to the previous idea. Return True if moved back, False if at start."""
        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Conversational Pacing Proxy - Human-like conversational pacing for LLMs"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("prompt", help="User prompt or question")
    ask_parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Upstream LLM model identifier (default: gpt-4o-mini)",
    )
    ask_parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (defaults to OPENAI_API_KEY env var)",
    )
    ask_parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Always hide diagrams, even if present in upstream output",
    )
    ask_parser.add_argument(
        "--debug",
        action="store_true",
        help="Print validator decisions: extra tokens and whether diagram was hidden",
    )
    ask_parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("./runs"),
        help="Directory for run logs (default: ./runs)",
    )
    ask_parser.add_argument(
        "--no-nlp-shadow",
        action="store_true",
        help="Disable shadow NLP diagram logging (default: enabled)",
    )
    ask_parser.add_argument(
        "--map-first",
        action="store_true",
        default=False,
        help="Generate and show system concept map before ideas (default: False)",
    )
    ask_parser.add_argument(
        "--no-idea-diagrams",
        action="store_true",
        default=False,
        help="Skip per-idea diagram generation (evaluation helper)",
    )
    
    # replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a previous run")
    replay_parser.add_argument("run_path", type=Path, help="Path to run directory")
    replay_parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Hide diagrams even if present on disk",
    )
    replay_parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug info about diagrams",
    )

    args = parser.parse_args()

    if args.command == "ask":
        try:
            llm_client = LLMClient(model=args.model, api_key=args.api_key)
            proxy = ConversationProxy(
                llm_client,
                no_diagrams=args.no_diagrams,
                debug=args.debug,
                log_dir=args.log_dir,
                nlp_shadow=not args.no_nlp_shadow,
                map_first=args.map_first,
                no_idea_diagrams=args.no_idea_diagrams,
            )
            print(f"Processing: {args.prompt}\n")
            proxy.start_conversation(args.prompt)
            
            # Show concept map first if map_first mode
            if args.map_first and proxy.concept_map_text:
                print("System Map")
                print("-" * 50)
                print(proxy.concept_map_text)
                print("-" * 50)
                print("Press Enter to start ideas...")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("\n\nGoodbye!")
                    sys.exit(0)
                print()
            
            run_interactive_loop(proxy, is_replay=False)
            proxy.finalize_run()
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            import traceback
            if args.debug:
                traceback.print_exc()
            sys.exit(1)
    elif args.command == "replay":
        try:
            if not args.run_path.exists():
                print(f"Error: Run directory not found: {args.run_path}", file=sys.stderr)
                sys.exit(1)
            
            proxy = ReplayProxy(
                args.run_path,
                no_diagrams=args.no_diagrams,
                debug=args.debug,
            )
            print(f"Replaying: {args.run_path}\n")
            
            # Show concept map first if it exists
            if proxy.concept_map_text:
                print("System Map")
                print("-" * 50)
                print(proxy.concept_map_text)
                print("-" * 50)
                print("Press Enter to start ideas...")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("\n\nGoodbye!")
                    sys.exit(0)
                print()
            
            run_interactive_loop(proxy, is_replay=True)
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            import traceback
            if args.debug:
                traceback.print_exc()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
