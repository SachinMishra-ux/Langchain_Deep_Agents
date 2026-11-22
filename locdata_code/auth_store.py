"""Authentication and credential management for LocData Code."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from locdata_code.paths import get_locdata_home

# Load existing environment variables
load_dotenv()


class AuthStore:
    """Manages credentials across environment variables and ~/.locdata/auth.json."""

    @classmethod
    def get_auth_file_path(cls) -> Path:
        return get_locdata_home() / "auth.json"

    @classmethod
    def load_stored_credentials(cls) -> dict[str, str]:
        """Load credentials from ~/.locdata/auth.json."""
        path = cls.get_auth_file_path()
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def save_credential(cls, key: str, value: str) -> None:
        """Save a credential to ~/.locdata/auth.json."""
        path = cls.get_auth_file_path()
        creds = cls.load_stored_credentials()
        creds[key] = value
        with open(path, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)

    @classmethod
    def get_key(cls, env_var_name: str) -> str | None:
        """Retrieve key from environment or fallback to stored file."""
        if os.environ.get(env_var_name):
            return os.environ[env_var_name]
        stored = cls.load_stored_credentials()
        return stored.get(env_var_name)

    @classmethod
    def get_available_providers(cls) -> dict[str, bool]:
        """Return status of all supported providers."""
        return {
            "sensenova": bool(cls.get_key("SENSENOVA_API_KEY")),
            "anthropic": bool(cls.get_key("ANTHROPIC_API_KEY")),
            "openai": bool(cls.get_key("OPENAI_API_KEY")),
            "gemini": bool(cls.get_key("GOOGLE_API_KEY") or cls.get_key("GEMINI_API_KEY")),
            "ollama": bool(os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_MODEL")),
        }
