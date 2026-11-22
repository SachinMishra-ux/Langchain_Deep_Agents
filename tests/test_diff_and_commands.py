"""Unit tests for diff utilities and command registry."""

from locdata_code.command_registry import match_command, COMMAND_CATALOG
from locdata_code.diff_utils import create_unified_diff, create_edit_preview


def test_command_matching():
    help_cmd = match_command("/help")
    assert help_cmd is not None
    assert help_cmd.name == "/help"

    alias_cmd = match_command("/?")
    assert alias_cmd is not None
    assert alias_cmd.name == "/help"

    exit_cmd = match_command("/q")
    assert exit_cmd is not None
    assert exit_cmd.name == "/exit"

    assert match_command("/unknown_command_xyz") is None


def test_diff_creation():
    old = "def add(a, b):\n    return a - b\n"
    new = "def add(a, b):\n    return a + b\n"
    diff = create_unified_diff(old, new, "math_utils.py")
    assert "-    return a - b" in diff
    assert "+    return a + b" in diff


def test_edit_preview():
    existing = "line1\nline2\nline3\n"
    preview = create_edit_preview(existing, "line2", "line_updated", "sample.txt")
    assert "-line2" in preview
    assert "+line_updated" in preview
