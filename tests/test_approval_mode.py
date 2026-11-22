"""Unit tests for approval modes and auto safety heuristics."""

from locdata_code.approval_mode import ApprovalMode, is_action_safe_under_auto


def test_approval_mode_parsing():
    assert ApprovalMode.from_str("bypass") == ApprovalMode.BYPASS
    assert ApprovalMode.from_str("auto") == ApprovalMode.AUTO
    assert ApprovalMode.from_str("prompt") == ApprovalMode.PROMPT
    assert ApprovalMode.from_str(None) == ApprovalMode.PROMPT


def test_auto_safety_read_tools():
    assert is_action_safe_under_auto("ls", {}) is True
    assert is_action_safe_under_auto("read_file", {"file_path": "test.py"}) is True
    assert is_action_safe_under_auto("glob", {"pattern": "*.py"}) is True
    assert is_action_safe_under_auto("web_search", {"query": "python"}) is True


def test_auto_safety_dangerous_commands():
    assert is_action_safe_under_auto("execute", {"command": "pytest"}) is True
    assert is_action_safe_under_auto("execute", {"command": "git status"}) is True
    assert is_action_safe_under_auto("execute", {"command": "rm -rf /tmp/data"}) is False
    assert is_action_safe_under_auto("execute", {"command": "git push origin main --force"}) is False
