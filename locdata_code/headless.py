"""Headless non-interactive execution engine for LocData Code (-x mode)."""

from __future__ import annotations

import json
import sys
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from locdata_code.agent import create_locdata_agent
from locdata_code.approval_mode import ApprovalMode, is_action_safe_under_auto
from locdata_code.config import LocDataConfig


def run_headless_task(
    task_prompt: str,
    config: LocDataConfig,
    json_mode: bool = False,
    session_id: str = "locdata-headless",
) -> int:
    """Execute a single task non-interactively and return exit code (0 for success)."""
    console = Console(stderr=json_mode)  # In JSON mode, write prose to stderr

    if not json_mode:
        console.print(
            Panel.fit(
                f"[bold cyan]LocData Code (Headless Mode)[/bold cyan]\n"
                f"[dim]Task:[/dim] {task_prompt}",
                border_style="cyan",
            )
        )

    agent = create_locdata_agent(config)
    thread_config = {"configurable": {"thread_id": session_id}}

    final_response_content = ""
    success = True

    try:
        events = agent.stream(
            {"messages": [HumanMessage(content=task_prompt)]},
            config=thread_config,
            stream_mode="updates",
        )

        for event in events:
            for node_name, node_output in event.items():
                if node_output and isinstance(node_output, dict) and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            # Tool call requested
                            if msg.tool_calls:
                                for tc in msg.tool_calls:
                                    t_name = tc.get("name")
                                    t_args = tc.get("args", {})
                                    if json_mode:
                                        print(json.dumps({"event": "tool_call", "name": t_name, "args": t_args}))
                                    else:
                                        console.print(
                                            f"[bold magenta]⚙ Tool Call:[/bold magenta] "
                                            f"[bold]{t_name}[/bold] -> [dim]{t_args}[/dim]"
                                        )
                            elif msg.content:
                                final_response_content = str(msg.content)

                        elif isinstance(msg, ToolMessage):
                            preview = str(msg.content)[:180].replace("\n", " ")
                            if json_mode:
                                print(json.dumps({"event": "tool_result", "name": msg.name, "result": str(msg.content)[:500]}))
                            else:
                                console.print(
                                    f"[dim cyan]↳ Result [{msg.name}]:[/dim cyan] [dim]{preview}...[/dim]"
                                )

        if not json_mode and final_response_content:
            console.print()
            console.print(
                Panel(
                    Markdown(final_response_content),
                    title="[bold green]LocData Code Complete[/bold green]",
                    border_style="green",
                )
            )
        elif json_mode:
            print(json.dumps({"event": "complete", "response": final_response_content}))

    except Exception as e:
        success = False
        if json_mode:
            print(json.dumps({"event": "error", "error": str(e)}))
        else:
            console.print(f"[bold red]Headless execution error:[/bold red] {e}")
        return 1

    return 0 if success else 1
