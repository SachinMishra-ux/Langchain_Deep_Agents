"""Diff and patch inspection utilities for LocData Code."""

from __future__ import annotations

import difflib
from pathlib import Path
from rich.syntax import Syntax
from rich.text import Text


def create_unified_diff(
    old_content: str,
    new_content: str,
    file_path: str = "file",
) -> str:
    """Generate a standard unified diff string between old and new file content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    )
    return "".join(diff)


def create_edit_preview(
    existing_content: str,
    target: str,
    replacement: str,
    file_path: str = "file",
) -> str:
    """Preview an exact target replacement edit as a unified diff."""
    if target not in existing_content:
        return f"[Diff Warning: Target string not found in {file_path}]"
    new_content = existing_content.replace(target, replacement, 1)
    return create_unified_diff(existing_content, new_content, file_path)


def render_colored_diff(diff_text: str) -> Text:
    """Render a unified diff text into a Rich Text object with colored additions/deletions."""
    text = Text()
    for line in diff_text.splitlines():
        if line.startswith("---") or line.startswith("+++"):
            text.append(line + "\n", style="bold cyan")
        elif line.startswith("@@"):
            text.append(line + "\n", style="bold magenta")
        elif line.startswith("+"):
            text.append(line + "\n", style="green")
        elif line.startswith("-"):
            text.append(line + "\n", style="red")
        else:
            text.append(line + "\n", style="dim")
    return text
