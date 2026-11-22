"""Configuration management for LocData Code."""

from __future__ import annotations

import os
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

from locdata_code.approval_mode import ApprovalMode
from locdata_code.paths import get_global_config_path, get_project_config_path


@dataclass
class ModelConfig:
    """Model provider configuration."""

    provider: str = "auto"
    model: str = "auto"
    temperature: float = 0.2
    max_tokens: int | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None


@dataclass
class LocDataConfig:
    """Unified configuration for LocData Code."""

    model: ModelConfig = field(default_factory=ModelConfig)
    approval_mode: ApprovalMode = ApprovalMode.PROMPT
    enable_web_search: bool = True
    enable_subagents: bool = True
    max_search_results: int = 5
    project_root: str = "."
    verbose: bool = False

    @classmethod
    def load(cls, project_root: str | Path | None = None) -> LocDataConfig:
        """Load configuration hierarchy: Defaults -> Global TOML -> Project TOML -> Env."""
        cfg = cls()
        root = Path(project_root or os.getcwd()).resolve()
        cfg.project_root = str(root)

        # 1. Global config (~/.locdata/config.toml)
        global_path = get_global_config_path()
        if global_path.exists():
            try:
                with open(global_path, "rb") as f:
                    data = tomllib.load(f)
                    cfg._merge_dict(data)
            except Exception:
                pass

        # 2. Project config (./.locdata/config.toml)
        proj_path = get_project_config_path(root)
        if proj_path.exists():
            try:
                with open(proj_path, "rb") as f:
                    data = tomllib.load(f)
                    cfg._merge_dict(data)
            except Exception:
                pass

        # 3. Environment variable overrides
        if os.environ.get("LOCDATA_MODEL"):
            cfg.model.model = os.environ["LOCDATA_MODEL"]
        if os.environ.get("LOCDATA_APPROVAL"):
            cfg.approval_mode = ApprovalMode.from_str(os.environ["LOCDATA_APPROVAL"])

        return cfg

    def _merge_dict(self, data: dict[str, Any]) -> None:
        """Merge a TOML dictionary into this configuration."""
        if "approval_mode" in data:
            self.approval_mode = ApprovalMode.from_str(data["approval_mode"])
        if "enable_web_search" in data:
            self.enable_web_search = bool(data["enable_web_search"])
        if "verbose" in data:
            self.verbose = bool(data["verbose"])

        if "model" in data and isinstance(data["model"], dict):
            m = data["model"]
            if "provider" in m:
                self.model.provider = m["provider"]
            if "model" in m:
                self.model.model = m["model"]
            if "temperature" in m:
                self.model.temperature = float(m["temperature"])
            if "base_url" in m:
                self.model.base_url = m["base_url"]

    def _clean_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        """Recursively strip None values so tomli_w doesn't fail."""
        cleaned = {}
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, dict):
                cleaned[k] = self._clean_dict(v)
            else:
                cleaned[k] = v
        return cleaned

    def save_global(self) -> None:
        """Persist current configuration to global config file."""
        path = get_global_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_data = {
            "approval_mode": self.approval_mode.value,
            "enable_web_search": self.enable_web_search,
            "model": asdict(self.model),
        }
        data = self._clean_dict(raw_data)
        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    def save_project(self, project_root: str | Path | None = None) -> None:
        """Persist current configuration to project config file."""
        path = get_project_config_path(project_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_data = {
            "approval_mode": self.approval_mode.value,
            "enable_web_search": self.enable_web_search,
            "model": asdict(self.model),
        }
        data = self._clean_dict(raw_data)
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
