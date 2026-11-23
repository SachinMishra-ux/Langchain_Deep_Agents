"""MCP configuration and server management for LocData Code."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool

from locdata_code.paths import get_locdata_home, get_project_locdata_dir

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an external MCP server."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class MCPManager:
    """Discovers and parses MCP server configurations and loads tools."""

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

    @classmethod
    def load_mcp_tools(cls, project_root: str | Path | None = None) -> list[BaseTool]:
        """Discover configured MCP servers and load their tools via MultiServerMCPClient."""
        servers = cls.discover_servers(project_root)
        if not servers:
            return []

        connections: dict[str, Any] = {}
        for s in servers:
            if not s.enabled:
                continue
            if s.command:
                connections[s.name] = {
                    "command": s.command,
                    "args": s.args,
                    "env": s.env or None,
                    "transport": "stdio",
                }

        if not connections:
            return []

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            client = MultiServerMCPClient(connections)

            # Check if there is already a running asyncio loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    raw_tools = pool.submit(lambda: asyncio.run(client.get_tools())).result(timeout=10)
            else:
                raw_tools = asyncio.run(client.get_tools())

            # Adapt tools to support both sync and async invocations
            from langchain_core.tools import StructuredTool
            adapted_tools: list[BaseTool] = []
            for t in raw_tools:
                if isinstance(t, StructuredTool) and t.func is None and t.coroutine is not None:
                    coro = t.coroutine
                    def _make_sync(target_coro):
                        def _sync_runner(**kwargs):
                            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as worker_pool:
                                return worker_pool.submit(lambda: asyncio.run(target_coro(**kwargs))).result(timeout=30)
                        return _sync_runner

                    wrapped = StructuredTool(
                        name=t.name,
                        description=t.description,
                        args_schema=t.args_schema,
                        func=_make_sync(coro),
                        coroutine=coro,
                    )
                    adapted_tools.append(wrapped)
                else:
                    adapted_tools.append(t)

            return adapted_tools
        except Exception as e:
            logger.warning("Failed to load MCP tools: %s", e)
            return []
