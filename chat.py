"""
Chat with the matching agent in the terminal.

  python chat.py                                               # type messages yourself
  python chat.py --jd job_descriptions/frontend_engineer.txt   # open with a job description file
  python chat.py --script scenarios/01_react_search.txt        # replay a scripted conversation

The graph runs until it reaches human_feedback, where interrupt() pauses it. This loop
then reads the next message and resumes the graph with Command(resume=message). While a
node runs, its progress lines and tool calls are streamed so you can watch it work.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Quieten the embedding model's start-up chatter before anything imports it.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")  # the hub sets its own log level from this on import
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
logging.getLogger("torch.distributed.elastic.multiprocessing.redirects").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from dotenv import load_dotenv  # noqa: E402
from langgraph.types import Command  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402

from corpus import CorpusError  # noqa: E402
from llm import LLMError  # noqa: E402
from matching_agent import MAX_MESSAGE_CHARS, QUIT_WORDS, MatchingAgent  # noqa: E402

NODE_LABELS = {
    "parse_jd": "Parse JD",
    "extract_requirements": "Extract requirements",
    "search_resumes": "Search resumes - Round 1",
    "rank_candidates": "Rank candidates - Round 2",
    "generate_report": "Generate report - Round 3",
    "agent_turn": "Agent answered",
}
GREETING = ("Describe who you are looking for in one line, or give a job description file such as "
            "job_descriptions/frontend_engineer.txt. Type quit to leave.")

console = Console()


def stream(app, graph_input, config) -> None:
    """Run the graph until it pauses or ends, printing progress and new assistant messages."""
    for mode, chunk in app.stream(graph_input, config, stream_mode=["updates", "custom"]):
        if mode == "custom":
            console.print(f"  [dim]{chunk['progress']}[/dim]")
            continue
        for node, update in chunk.items():
            if node not in NODE_LABELS:  # human_feedback, and the "__interrupt__" marker when the graph pauses
                continue
            console.print(f"[cyan]✓ {NODE_LABELS[node]}[/cyan]")
            for message in (update or {}).get("messages", []):
                if message["role"] == "assistant":
                    console.print(Panel(Markdown(message["content"]), title="Agent", border_style="green"))


def read_script(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text().splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def ask(prompt: str) -> str:
    try:
        return console.input(prompt).strip()
    except (EOFError, KeyboardInterrupt):  # Ctrl-D, Ctrl-C or a closed input stream
        return "quit"


def next_message(script: list[str] | None, pause: float) -> str:
    if script is None:
        return ask("[bold]You:[/bold] ")
    if not script:
        return "quit"
    time.sleep(pause)
    message = script.pop(0)
    console.print(f"[bold]You:[/bold] {message}")
    return message


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the resume matching agent.")
    parser.add_argument("--jd", help="Open with this job description (text or a path under job_descriptions/)")
    parser.add_argument("--script", type=Path, help="Replay user messages from a file, one per line")
    parser.add_argument("--pause", type=float, default=0.0, help="Seconds to wait before each scripted message")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parent / ".env")

    script = read_script(args.script) if args.script else None
    agent = MatchingAgent()
    app = agent.build()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    console.print(Panel(GREETING, title="Agentic Profile Matching", border_style="cyan"))

    first = args.jd or next_message(script, args.pause)
    while len(first) > MAX_MESSAGE_CHARS:
        console.print(f"[red]That message is {len(first):,} characters; the limit is {MAX_MESSAGE_CHARS:,}. "
                      "Save a long job description to a file in job_descriptions/ and give its path.[/red]")
        first = next_message(script, args.pause)
    if not first or first.lower() in QUIT_WORDS:
        return
    graph_input = {"messages": [{"role": "user", "content": first}], "jd_input": first}
    while True:
        try:
            stream(app, graph_input, config)
            failure = None
        except (LLMError, CorpusError) as exc:
            failure = f"That step failed: {exc}"
        except Exception as exc:  # a bug: show it, but keep the conversation so the user can retry
            failure = f"Unexpected error ({type(exc).__name__}): {exc}"
        if failure:
            console.print(f"[red]{failure}[/red]")
            if script is not None:  # nobody is at the keyboard to decide whether to retry
                sys.exit(1)
            if ask("Press Enter to retry, or type quit: ").lower() in QUIT_WORDS:
                return
            graph_input = None  # None resumes the graph at the step that failed
            continue
        if not app.get_state(config).next:  # the graph reached END
            u = agent.claude.usage
            console.print(f"[cyan]Goodbye.[/cyan] [dim]Claude usage: {u['calls']} calls, {u['input_tokens']:,} input "
                          f"tokens (+{u['cache_read_input_tokens']:,} from cache), {u['output_tokens']:,} output "
                          f"tokens on {agent.claude.model}.[/dim]")
            return
        message = next_message(script, args.pause)
        graph_input = Command(resume=message)


if __name__ == "__main__":
    main()
