"""Core agent assembly and model resolution for LocData Code."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from locdata_code.auth_store import AuthStore
from locdata_code.config import LocDataConfig
from locdata_code.paths import get_project_memory_path
from locdata_code.skills.loader import SkillManager
from locdata_code.tools.web_search import web_search

LOCDATA_SYSTEM_PROMPT = """You are **LocData Code**, an autonomous, enterprise-grade AI software engineer and universal problem solver.

You operate directly inside the user's workspace with full authority to read, edit, execute, build, test, and research.

### CORE OPERATING PRINCIPLES:
1. **Plan & Decompose:** For complex tasks, outline a concise plan before taking destructive actions.
2. **Inspect Before Changing:** Never guess or overwrite blindly. Use `glob`, `grep`, and `read_file` to understand the codebase first.
3. **Surgical Precision (`edit_file`):** Prefer `edit_file` with exact string matches for code modifications. Do not rewrite 500-line files when editing 5 lines.
4. **Active Verification (`execute`):** After making changes, always run verification commands (e.g. `pytest`, `npm test`, python syntax checks) using `execute` before declaring success.
5. **Real-Time Web Grounding (`web_search`):** When encountering unfamiliar errors, third-party libraries, or latest API specifications, use `web_search`.
6. **Context Efficiency:** Deep Agents offloads large outputs to virtual storage. Inspect specific line ranges or grep matching patterns rather than requesting huge dumps.
"""


def resolve_model(
    config: LocDataConfig,
) -> BaseChatModel:
    """Resolve and instantiate the appropriate ChatModel based on config and available keys."""
    # 1. Explicit model string if provided (e.g. openai:gpt-4o or anthropic:claude-3-7-sonnet)
    custom_model = config.model.model
    if custom_model and custom_model != "auto":
        # Check if it has provider prefix
        if ":" in custom_model:
            provider, m_name = custom_model.split(":", 1)
            if provider == "openai":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=m_name, api_key=AuthStore.get_key("OPENAI_API_KEY"), temperature=config.model.temperature)
            if provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(model=m_name, api_key=AuthStore.get_key("ANTHROPIC_API_KEY"), temperature=config.model.temperature)
            if provider == "gemini" or provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(model=m_name, google_api_key=AuthStore.get_key("GOOGLE_API_KEY") or AuthStore.get_key("GEMINI_API_KEY"), temperature=config.model.temperature)

    # 2. SenseNova (Default if SENSENOVA_API_KEY is present)
    sensenova_key = AuthStore.get_key("SENSENOVA_API_KEY")
    if sensenova_key:
        from langchain_openai import ChatOpenAI
        m_name = custom_model if (custom_model and custom_model != "auto") else "sensenova-6.8-flash-lite"
        return ChatOpenAI(
            model=m_name,
            base_url=config.model.base_url or "https://token.sensenova.ai/v1",
            api_key=sensenova_key,
            temperature=config.model.temperature,
        )

    # 3. Anthropic Claude
    anthropic_key = AuthStore.get_key("ANTHROPIC_API_KEY")
    if anthropic_key:
        from langchain_anthropic import ChatAnthropic
        m_name = custom_model if (custom_model and custom_model != "auto") else "claude-3-7-sonnet-20250219"
        return ChatAnthropic(
            model=m_name,
            api_key=anthropic_key,
            temperature=config.model.temperature,
        )

    # 4. OpenAI
    openai_key = AuthStore.get_key("OPENAI_API_KEY")
    if openai_key:
        from langchain_openai import ChatOpenAI
        m_name = custom_model if (custom_model and custom_model != "auto") else "gpt-4o"
        return ChatOpenAI(
            model=m_name,
            api_key=openai_key,
            temperature=config.model.temperature,
        )

    # 5. Google Gemini
    google_key = AuthStore.get_key("GOOGLE_API_KEY") or AuthStore.get_key("GEMINI_API_KEY")
    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        m_name = custom_model if (custom_model and custom_model != "auto") else "gemini-2.0-flash"
        return ChatGoogleGenerativeAI(
            model=m_name,
            google_api_key=google_key,
            temperature=config.model.temperature,
        )

    # 6. Local Ollama (fallback)
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=custom_model if (custom_model and custom_model != "auto") else "llama3.1",
        base_url=ollama_url,
        api_key="ollama",
        temperature=config.model.temperature,
    )


def create_locdata_agent(
    config: LocDataConfig | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Build and compile the complete LocData Code Deep Agent graph."""
    if config is None:
        config = LocDataConfig.load()

    model = resolve_model(config)
    project_root = Path(config.project_root).resolve()

    # Backend: provides ls, glob, grep, read_file, edit_file, write_file, execute
    backend = LocalShellBackend(
        root_dir=project_root,
        virtual_mode=False,
        inherit_env=True,
    )

    # Assemble tools
    tools: list[Any] = []
    if config.enable_web_search:
        tools.append(web_search)

    # Assemble system instructions
    workspace_context = f"\n### WORKSPACE CONTEXT:\n- Current Workspace Root: `{project_root}`\n- Operate within this workspace. For listing and file operations, use relative paths (e.g., `.` or `./pyproject.toml`) or paths rooted at `{project_root}`.\n"
    prompt_parts = [LOCDATA_SYSTEM_PROMPT, workspace_context]

    # Ingest project memory (LOCDATA.md / AGENTS.md) if present
    memory_path = get_project_memory_path(project_root)
    if memory_path.exists():
        try:
            mem_content = memory_path.read_text(encoding="utf-8")
            prompt_parts.append(f"\n### PROJECT MEMORY & GUIDELINES ({memory_path.name}):\n{mem_content}")
        except Exception:
            pass

    # Ingest discovered skills
    skills = SkillManager.discover_skills(project_root)
    skills_prompt = SkillManager.format_skills_prompt(skills)
    if skills_prompt:
        prompt_parts.append(skills_prompt)

    full_system_prompt = "\n\n".join(prompt_parts)

    # Compile via Deep Agents
    agent_graph = create_deep_agent(
        model=model,
        backend=backend,
        tools=tools,
        system_prompt=full_system_prompt,
        checkpointer=checkpointer or MemorySaver(),
    )

    return agent_graph
