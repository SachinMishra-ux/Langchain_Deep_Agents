"""Main CLI entrypoint for LocData Code."""

from __future__ import annotations

import argparse
import sys
from locdata_code import __version__
from locdata_code.approval_mode import ApprovalMode
from locdata_code.config import LocDataConfig
from locdata_code.headless import run_headless_task
from locdata_code.paths import ensure_locdata_dirs
from locdata_code.tui.app import LocDataApp, run_interactive_repl


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for LocData Code."""
    parser = argparse.ArgumentParser(
        prog="loccode",
        description="LocData Code (loccode) - Autonomous AI Coding & Problem Solving Agent Harness",
    )
    parser.add_argument(
        "-x",
        "--execute",
        type=str,
        metavar="TASK",
        help="Execute a task headlessly (non-interactively) and exit with status code.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output events as JSON lines (useful for headless CI/CD integration).",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        help="Specify the LLM model to use (e.g. sensenova-6.8-flash-lite, gpt-4o, claude-3-7-sonnet).",
    )
    parser.add_argument(
        "-a",
        "--approval",
        type=str,
        choices=["prompt", "auto", "bypass"],
        help="Set execution approval mode: prompt (default), auto (safe actions only), bypass (autonomous).",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Run in standard interactive REPL mode instead of full-screen Textual TUI.",
    )
    parser.add_argument(
        "--resume",
        type=str,
        metavar="SESSION_ID",
        help="Resume a previous conversation session by ID.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"LocData Code v{__version__}",
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Optional initial prompt/task to run.",
    )
    return parser.parse_args(argv)


def cli_main() -> None:
    """Main CLI execution routine."""
    args = parse_args()
    ensure_locdata_dirs()

    # Load configuration
    config = LocDataConfig.load()
    if args.model:
        config.model.model = args.model
    if args.approval:
        config.approval_mode = ApprovalMode.from_str(args.approval)

    session_id = args.resume or f"locdata-session-{config.model.model}"

    # 1. Headless Execution (-x or positional query with non-interactive flag)
    task_prompt = args.execute or (" ".join(args.query) if args.query else None)

    if task_prompt:
        exit_code = run_headless_task(
            task_prompt=task_prompt,
            config=config,
            json_mode=args.json,
            session_id=session_id,
        )
        sys.exit(exit_code)

    # 2. Interactive Terminal UI or REPL
    # If not a tty or --repl requested, use Rich REPL
    if args.repl or not sys.stdin.isatty():
        run_interactive_repl(config, session_id=session_id)
    else:
        app = LocDataApp(config, session_id=session_id)
        app.run()


if __name__ == "__main__":
    cli_main()
