"""Path utilities for LocData Code."""

from __future__ import annotations

import os
from pathlib import Path


def get_locdata_home() -> Path:
    """Return the global LocData home directory (~/.locdata or $LOCDATA_HOME)."""
    env_home = os.environ.get("LOCDATA_HOME")
    if env_home:
        path = Path(env_home).expanduser().resolve()
    else:
        path = (Path.home() / ".locdata").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_locdata_dir(project_root: str | Path | None = None) -> Path:
    """Return the local project .locdata directory."""
    root = Path(project_root or os.getcwd()).resolve()
    loc_dir = root / ".locdata"
    return loc_dir


def get_sessions_db_path() -> Path:
    """Return the path to the SQLite sessions database."""
    return get_locdata_home() / "sessions.db"


def get_global_config_path() -> Path:
    """Return the global configuration file path."""
    return get_locdata_home() / "config.toml"


def get_project_config_path(project_root: str | Path | None = None) -> Path:
    """Return the project configuration file path."""
    return get_project_locdata_dir(project_root) / "config.toml"


def get_project_memory_path(project_root: str | Path | None = None) -> Path:
    """Return the project memory file path (LOCDATA.md or AGENTS.md)."""
    root = Path(project_root or os.getcwd()).resolve()
    primary = root / "LOCDATA.md"
    if primary.exists():
        return primary
    secondary = root / "AGENTS.md"
    if secondary.exists():
        return secondary
    return primary


def get_skills_dirs(project_root: str | Path | None = None) -> list[Path]:
    """Return search directories for skills."""
    dirs: list[Path] = [
        get_locdata_home() / "skills",
        get_project_locdata_dir(project_root) / "skills",
    ]
    return [d for d in dirs if d.exists()]


def ensure_locdata_dirs(project_root: str | Path | None = None) -> None:
    """Ensure required LocData directories exist."""
    home = get_locdata_home()
    (home / "skills").mkdir(parents=True, exist_ok=True)
    (home / "logs").mkdir(parents=True, exist_ok=True)
    get_project_locdata_dir(project_root).mkdir(parents=True, exist_ok=True)
