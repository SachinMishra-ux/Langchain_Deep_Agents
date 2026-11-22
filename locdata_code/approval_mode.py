"""Human-in-the-loop approval modes for LocData Code."""

from __future__ import annotations

import re
from enum import Enum


class ApprovalMode(str, Enum):
    """Execution approval mode for tool operations."""

    PROMPT = "prompt"  # Ask before executing modifying operations or shell commands
    AUTO = "auto"      # Automatically execute read/safe actions, prompt on high-risk actions
    BYPASS = "bypass"  # Execute all tool actions autonomously without user prompts

    @classmethod
    def from_str(cls, value: str | None) -> ApprovalMode:
        """Parse string to ApprovalMode with default to PROMPT."""
        if not value:
            return cls.PROMPT
        normalized = value.strip().lower()
        if normalized in ("bypass", "y", "yes", "auto-approve"):
            return cls.BYPASS
        if normalized in ("auto", "smart"):
            return cls.AUTO
        return cls.PROMPT


# Regex patterns considered dangerous for AUTO mode
DANGEROUS_COMMAND_PATTERNS = [
    r"\brm\s+-(?:r|f|rf|fr)\b",
    r"\bgit\s+push\s+.*--force\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bdrop\s+database\b",
    r"\bdrop\s+table\b",
    r"\bchmod\s+-R\s+777\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\(\)\{ :\|:& \};:",  # fork bomb
]


def is_action_safe_under_auto(tool_name: str, tool_args: dict) -> bool:
    """Determine if a tool call is safe to auto-execute without human prompt."""
    # Read-only tools are always safe
    if tool_name in ("ls", "read_file", "glob", "grep", "web_search", "task"):
        return True

    # Shell execution inspection
    if tool_name == "execute":
        command = tool_args.get("command", "")
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False
        # General non-destructive shell commands are allowed in auto mode
        return True

    # Modifying files in project directory is allowed in auto mode unless outside root
    if tool_name in ("write_file", "edit_file"):
        path = str(tool_args.get("file_path", ""))
        if path.startswith("/etc") or path.startswith("/sys") or ".." in path:
            return False
        return True

    return False
