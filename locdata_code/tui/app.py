"""Textual interactive application and REPL runner for LocData Code."""

from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Input, Static

from locdata_code.agent import create_locdata_agent
from locdata_code.command_registry import COMMAND_CATALOG, match_command
from locdata_code.config import LocDataConfig
from locdata_code.tui.theme import LOCDATA_BANNER, LOCDATA_TAGLINE
from locdata_code.tui.widgets import ChatStream, MessageBubble, StatusBar, ToolCallBubble


def get_current_git_branch() -> str:
    """Detect the current git branch name."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "workspace"


class LocDataApp(App):
    """Full-screen interactive Textual application for LocData Code."""

    TITLE = "LocData Code"
    SUB_TITLE = "Autonomous Problem Solving Agent"
    CSS = """
    Screen {
        background: #0f141c;
    }
    #input-container {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: #1e2630;
    }
    Input {
        width: 100%;
        border: tall #00d2ff;
        background: #121820;
        color: #eceff1;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_screen", "Clear Screen", show=True),
    ]

    def __init__(self, config: LocDataConfig, session_id: str = "locdata-tui"):
        super().__init__()
        self.config_data = config
        self.session_id = session_id
        self.agent = create_locdata_agent(self.config_data)
        self.thread_config = {"configurable": {"thread_id": self.session_id}}
        self.branch = get_current_git_branch()

    def compose(self) -> ComposeResult:
        model_display = self.config_data.model.model or "sensenova"
        yield StatusBar(
            model_name=model_display,
            approval_mode=self.config_data.approval_mode.value,
            git_branch=self.branch,
        )
        yield ChatStream(id="chat-stream")
        with Vertical(id="input-container"):
            yield Input(
                placeholder="Ask LocData Code a question, request a fix, or type /help...",
                id="prompt-input",
            )
        yield Footer()

    async def on_mount(self) -> None:
        """Post initial welcome banner upon mount."""
        stream = self.query_one("#chat-stream", ChatStream)
        welcome_text = (
            f"```\n{LOCDATA_BANNER}\n```\n"
            f"**{LOCDATA_TAGLINE}**\n\n"
            f"• **Approval Mode:** `{self.config_data.approval_mode.value}`\n"
            f"• **Workspace:** `{self.config_data.project_root}`\n"
            f"• Type `/help` for commands or start typing your task below."
        )
        stream.mount(MessageBubble("agent", welcome_text))
        self.query_one("#prompt-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_text = event.value.strip()
        if not user_text:
            return

        input_widget = self.query_one("#prompt-input", Input)
        input_widget.value = ""
        stream = self.query_one("#chat-stream", ChatStream)

        # Handle Slash Commands
        if user_text.startswith("/"):
            await self._handle_slash_command(user_text, stream)
            return

        # Render User Message
        stream.mount(MessageBubble("user", user_text))
        stream.scroll_end(animate=True)

        # Run agent in background task
        asyncio.create_task(self._run_agent_turn(user_text, stream))

    async def _handle_slash_command(self, cmd_text: str, stream: ChatStream) -> None:
        matched = match_command(cmd_text)
        parts = cmd_text.split()
        cmd_name = parts[0].lower()

        if cmd_name in ("/exit", "/quit", "/q"):
            self.exit()
            return

        if cmd_name in ("/clear", "/reset"):
            stream.remove_children()
            stream.mount(MessageBubble("agent", "🧹 *Conversation cleared. New thread initialized.*"))
            self.session_id = f"locdata-{os.urandom(4).hex()}"
            self.thread_config = {"configurable": {"thread_id": self.session_id}}
            return

        if cmd_name in ("/help", "/?"):
            help_md = "### LocData Code Slash Commands:\n"
            for c in COMMAND_CATALOG:
                aliases_str = f" (aliases: {', '.join(c.aliases)})" if c.aliases else ""
                help_md += f"- **`{c.name}`** `{c.argument_hint}`: {c.description}{aliases_str}\n"
            stream.mount(MessageBubble("agent", help_md))
            stream.scroll_end(animate=True)
            return

        if cmd_name == "/approval" and len(parts) > 1:
            from locdata_code.approval_mode import ApprovalMode
            self.config_data.approval_mode = ApprovalMode.from_str(parts[1])
            stream.mount(MessageBubble("agent", f"Approval mode updated to: `{self.config_data.approval_mode.value}`"))
            return

        stream.mount(MessageBubble("agent", f"Command `{cmd_text}` recognized. (Use `/help` for list of commands)"))

    async def _run_agent_turn(self, user_prompt: str, stream: ChatStream) -> None:
        """Execute agent turn asynchronously and stream updates into the chat UI."""
        def run_stream():
            return list(
                self.agent.stream(
                    {"messages": [HumanMessage(content=user_prompt)]},
                    config=self.thread_config,
                    stream_mode="updates",
                )
            )

        try:
            loop = asyncio.get_running_loop()
            events = await loop.run_in_executor(None, run_stream)
            final_content = ""

            for event in events:
                for node_name, node_output in event.items():
                    if node_output and isinstance(node_output, dict) and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, AIMessage):
                                if msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        t_name = tc.get("name", "")
                                        t_args = tc.get("args", {})
                                        stream.mount(ToolCallBubble(t_name, t_args))
                                elif msg.content:
                                    final_content = str(msg.content)
                            elif isinstance(msg, ToolMessage):
                                preview = str(msg.content)[:120].replace("\n", " ")
                                stream.mount(ToolCallBubble(msg.name, {}, preview))

            if final_content:
                stream.mount(MessageBubble("agent", final_content))
            stream.scroll_end(animate=True)

        except Exception as e:
            stream.mount(MessageBubble("agent", f"**Execution Error:** `{e}`"))
            stream.scroll_end(animate=True)

    def action_clear_screen(self) -> None:
        stream = self.query_one("#chat-stream", ChatStream)
        stream.remove_children()


def run_interactive_repl(config: LocDataConfig, session_id: str = "locdata-repl") -> None:
    """Rich fallback interactive REPL for environments without alternate screen buffer support."""
    console = Console()
    console.print(
        Panel.fit(
            f"[bold cyan]{LOCDATA_BANNER}[/bold cyan]\n"
            f"[bold white]{LOCDATA_TAGLINE}[/bold white]\n\n"
            f"[dim]Model:[/dim] {config.model.model} · [dim]Approval:[/dim] {config.approval_mode.value}\n"
            f"[dim]Commands:[/dim] /help · /clear · /approval · /diff · /exit",
            border_style="cyan",
        )
    )

    agent = create_locdata_agent(config)
    thread_config = {"configurable": {"thread_id": session_id}}

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]loccode[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session exited. Goodbye![/yellow]")
            break

        cleaned = user_input.strip()
        if not cleaned:
            continue

        if cleaned in ("/exit", "/quit", "/q", "exit", "quit"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        if cleaned in ("/clear", "/reset", "clear"):
            session_id = f"locdata-{os.urandom(4).hex()}"
            thread_config = {"configurable": {"thread_id": session_id}}
            console.print("[green]Session reset. New thread created.[/green]")
            continue

        if cleaned in ("/help", "/?"):
            for c in COMMAND_CATALOG:
                console.print(f"[bold yellow]{c.name:12}[/bold yellow] {c.description}")
            continue

        console.print("[dim]Thinking & executing...[/dim]")

        try:
            final_content = ""
            for event in agent.stream(
                {"messages": [HumanMessage(content=cleaned)]},
                config=thread_config,
                stream_mode="updates",
            ):
                for node_name, node_output in event.items():
                    if node_output and isinstance(node_output, dict) and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, AIMessage):
                                if msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        console.print(
                                            f"[bold magenta]⚙ Tool Call:[/bold magenta] "
                                            f"[bold]{tc.get('name')}[/bold] -> [dim]{tc.get('args')}[/dim]"
                                        )
                                elif msg.content:
                                    final_content = str(msg.content)
                            elif isinstance(msg, ToolMessage):
                                preview = str(msg.content)[:180].replace("\n", " ")
                                console.print(
                                    f"[dim cyan]↳ Result [{msg.name}]:[/dim cyan] [dim]{preview}...[/dim]"
                                )

            if final_content:
                console.print()
                console.print(
                    Panel(
                        Markdown(final_content),
                        title="[bold green]LocData Code[/bold green]",
                        border_style="green",
                    )
                )
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
