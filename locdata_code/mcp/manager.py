"""MCP configuration and server management for LocData Code."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from locdata_code.paths import get_locdata_home, get_project_locdata_dir


@dataclass
class MCPServerConfig:
    """Configuration for an external MCP server."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class MCPManager:
    """Discovers and parses MCP server configurations."""

    @classmethod
    def get_config_paths(cls, project_root: str | Path | None = None) -> list[Path]:
        """Paths to check for MCP server configurations."""
        root = Path(project_root or ".").resolve()
        return [
            root / ".mcp.json",
            get_project_locdata_dir(root) / "mcp.json",
            get_locdata_home() / "mcp.json",
        ]

    @classmethod
    def discover_servers(cls, project_root: str | Path | None = None) -> list[MCPServerConfig]:
        """Discover all configured MCP servers."""
        servers: list[MCPServerConfig] = []
        for p in cls.get_config_paths(project_root):
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    mcp_servers = data.get("mcpServers", {})
                    for name, s_cfg in mcp_servers.items():
                        cmd = s_cfg.get("command", "")
                        args = s_cfg.get("args", [])
                        env = s_cfg.get("env", {})
                        servers.append(
                            MCPServerConfig(
                                name=name,
                                command=cmd,
                                args=args,
                                env=env,
                                enabled=True,
                            )
                        )
                except Exception:
                    continue
        return servers
