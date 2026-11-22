"""Textual UI widgets for LocData Code."""

from __future__ import annotations

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from locdata_code.tui import theme


class ChatStream(VerticalScroll):
    """Scrollable container for conversation messages and tool calls."""

    DEFAULT_CSS = """
    ChatStream {
        width: 100%;
        height: 1fr;
        padding: 1;
        background: #0f141c;
    }
    """


class MessageBubble(Static):
    """Widget rendering a user or assistant message."""

    def __init__(self, sender: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.sender = sender
        self.content_text = content

    def compose(self) -> ComposeResult:
        if self.sender == "user":
            panel = Panel(
                Text(self.content_text, style="bold white"),
                title="[bold cyan]You[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
        else:
            panel = Panel(
                Markdown(self.content_text),
                title="[bold green]LocData Code[/bold green]",
                border_style="green",
                padding=(0, 1),
            )
        yield Static(panel)


class ToolCallBubble(Static):
    """Widget rendering an executing or completed tool call."""

    def __init__(self, tool_name: str, args: dict, result_preview: str = "", **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.args = args
        self.result_preview = result_preview

    def compose(self) -> ComposeResult:
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.args.items())
        if len(args_str) > 80:
            args_str = args_str[:77] + "..."

        text = Text()
        text.append("⚙ Tool: ", style="bold magenta")
        text.append(f"{self.tool_name}({args_str})\n", style="bold white")
        if self.result_preview:
            text.append(f"  ↳ {self.result_preview}", style="dim cyan")

        yield Static(
            Panel(text, border_style="dim magenta", padding=(0, 1))
        )


class StatusBar(Static):
    """Top status bar displaying active model, git branch, and approval mode."""

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: #1e2630;
        color: #eceff1;
        padding: 0 1;
    }
    """

    def __init__(self, model_name: str, approval_mode: str, git_branch: str = "main", **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name
        self.approval_mode = approval_mode
        self.git_branch = git_branch

    def render(self) -> str:
        return f" 🧠 LocData Code | Model: {self.model_name} | Branch: {self.git_branch} | Approval: {self.approval_mode} | Type /help for commands"
