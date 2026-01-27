"""CLI interface for Conversational Pacing Proxy."""

import sys
from typing import Optional, Dict, Any
from .proxy import ConversationProxy
from .llm import LLMClient


def format_chunk(chunk: Dict[str, Any], index: int) -> str:
    """Format a chunk for display.
    
    Args:
        chunk: Dict with 'idea' and optional 'diagram' keys
        index: Zero-based index of the chunk
        
    Returns:
        Formatted string with idea and optional diagram
    """
    lines = [f"Idea {index + 1}:"]
    lines.append(chunk['idea'])
    
    if chunk.get('diagram'):
        lines.append('')  # Blank line before diagram
        lines.append(chunk['diagram'])
    
    return '\n'.join(lines) + '\n'


def display_controls(has_next: bool) -> str:
    """Display control options."""
    controls = []
    if has_next:
        controls.append("[next] Continue")
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
        
        # Display current chunk
        print(f"\n{format_chunk(chunk, proxy.current_index)}")
        
        # Display controls
        print(display_controls(proxy.has_next()))
        
        # Get user input
        try:
            user_input = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break
        
        # Handle user input
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


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Conversational Pacing Proxy - Human-like conversational pacing for LLMs"
    )
    parser.add_argument(
        "command",
        choices=["ask"],
        help="Command to execute"
    )
    parser.add_argument(
        "prompt",
        help="User prompt or question"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Upstream LLM model identifier (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenAI API key (defaults to OPENAI_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    if args.command == "ask":
        try:
            # Initialize LLM client
            llm_client = LLMClient(model=args.model, api_key=args.api_key)
            
            # Initialize proxy
            proxy = ConversationProxy(llm_client)
            
            # Start conversation
            print(f"Processing: {args.prompt}\n")
            proxy.start_conversation(args.prompt)
            
            # Run interactive loop
            run_interactive_loop(proxy)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
