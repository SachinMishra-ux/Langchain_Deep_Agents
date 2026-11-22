"""Slash command catalog and registry for LocData Code."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class CommandEntry:
    """Metadata for a registered slash command."""

    name: str
    description: str
    argument_hint: str = ""
    aliases: tuple[str, ...] = ()


COMMAND_CATALOG: list[CommandEntry] = [
    CommandEntry(
        name="/help",
        description="Show all available slash commands and usage guide",
        aliases=("/?",),
    ),
    CommandEntry(
        name="/clear",
        description="Start a fresh conversation thread and reset state",
        aliases=("/reset",),
    ),
    CommandEntry(
        name="/model",
        description="View or switch the active LLM provider and model",
        argument_hint="[model_name]",
    ),
    CommandEntry(
        name="/approval",
        description="Set execution approval mode: prompt, auto, or bypass",
        argument_hint="[prompt|auto|bypass]",
    ),
    CommandEntry(
        name="/auth",
        description="Check connection status of API credentials or set a key",
        argument_hint="[provider] [api_key]",
        aliases=("/connect",),
    ),
    CommandEntry(
        name="/context",
        description="Audit context window usage and estimated token consumption",
    ),
    CommandEntry(
        name="/diff",
        description="Inspect all unstaged git diffs in the project workspace",
    ),
    CommandEntry(
        name="/skills",
        description="List active domain skills discovered from SKILL.md files",
    ),
    CommandEntry(
        name="/mcp",
        description="List active and configured Model Context Protocol (MCP) servers",
    ),
    CommandEntry(
        name="/exit",
        description="Quit LocData Code",
        aliases=("/quit", "/q"),
    ),
]


def match_command(input_str: str) -> CommandEntry | None:
    """Find a matching command from the catalog by canonical name or alias."""
    cmd_name = input_str.strip().split()[0].lower()
    for entry in COMMAND_CATALOG:
        if entry.name == cmd_name or cmd_name in entry.aliases:
            return entry
    return None
