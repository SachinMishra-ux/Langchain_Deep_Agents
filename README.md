# 🧠⚡ LocData Code (`loccode`)
### *The Autonomous AI Coding & Problem Solving Agent Harness*

```
  _                 _____        _          _____          _      
 | |               |  __ \      | |        / ____|        | |     
 | |     ___   ___ | |  | | __ _| |_ __ _ | |     ___   __| | ___ 
 | |    / _ \ / __|| |  | |/ _` | __/ _` || |    / _ \ / _` |/ _ \
 | |___| (_) | (__ | |__| | (_| | || (_| || |___| (_) | (_| |  __/
 |______\___/ \___||_____/ \__,_|\__\__,_| \_____\___/ \__,_|\___|
```

Just like typing `claude` opens Claude Code, typing **`loccode`** opens **LocData Code** directly from any directory in your terminal!

**LocData Code** is an open-source, production-grade autonomous agent harness built directly on **LangChain's Deep Agents SDK** and **LangGraph**. It delivers a complete terminal-based coding assistant—similar to Claude Code, Cursor, and Deep Agents Code (`dcode`)—with full support for any LLM provider, persistent memory, customizable skills, MCP tools, and safety approval modes.

---

## 🏛️ Architecture & System Design

```
┌────────────────────────────────────────────────────────────────────────┐
│                   LOCDATA CODE TUI / CLIENT LAYER                      │
│  • Built with Python Textual & Rich                                    │
│  • Streaming token & event renderer                                    │
│  • Interactive diff viewer & file-change inspector                     │
│  • Human-in-the-loop approval modal (Prompt / Auto / Bypass)           │
│  • 10+ Slash Commands (/help, /clear, /approval, /diff, /auth, etc.)   │
│  • Headless execution mode (-x "prompt", --json) for CI/CD pipelines   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Streaming Protocol / Local IPC
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  LOCDATA AGENT HARNESS (SERVER GRAPH)                  │
│  • Core Engine: create_deep_agent() + LocalShellBackend                │
│  • Filesystem Suite: ls, glob, grep, read_file, edit_file, write_file   │
│  • Shell Execution: execute bash commands, test suites (pytest), git   │
│  • Web Grounding: web_search via DuckDuckGo                            │
│  • Context Safety: _blob_offload.py, DeltaChannel, Summarization       │
│  • MCP Gateway: Dynamic tool loading from fastmcp / .mcp.json          │
│  • Long-Term Memory: LOCDATA.md & SQLite session persistence           │
│  • Skills Engine: On-demand loading of SKILL.md packages               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- 🖥️ **Interactive Terminal UI (TUI):** Full-screen terminal user interface powered by [Textual](https://textual.textualize.io/) with real-time streaming, syntax highlighting, and auto-scroll.
- 🤖 **Multi-Model Agnostic:** Works out of the box with **SenseNova** (`sensenova-6.8-flash-lite`, `sensenova-6.8-flash`), **Anthropic Claude** (`claude-3-7-sonnet`), **OpenAI** (`gpt-4o`, `o3-mini`), **Google Gemini** (`gemini-2.0-flash`), and local **Ollama** models.
- ⚡ **Headless CI/CD Mode (`-x` / `--json`):** Execute automated tasks non-interactively in GitHub Actions, Jenkins, or deployment pipelines. Returns exit code `0` on success.
- 🛡️ **Three Safety Approval Modes:**
  - `prompt` *(default)*: Prompts for confirmation before modifying files or executing shell commands.
  - `auto`: Uses safety heuristics to auto-execute read-only and non-destructive commands while flagging risky operations (e.g. `rm -rf`, `git reset --hard`).
  - `bypass`: Fully autonomous execution.
- 📂 **Precision Code Editing:** Avoids hallucinated full-file overwrites by using surgical exact-match replacements via `edit_file` with visual diff previews.
- 🔍 **Real-Time Web Search:** Ground answers and debug unknown error messages using live DuckDuckGo web searches.
- 🧠 **Persistent Session Memory:** Sessions are saved via LangGraph checkpointers, enabling `--resume <session_id>` across terminal reboots.
- 🔌 **Model Context Protocol (MCP):** Connect custom tools from external MCP servers via `.locdata/mcp.json` or `.mcp.json`.
- 🧩 **Extensible Skills:** Drop custom domain skills (`SKILL.md`) into `~/.locdata/skills/` or `./.locdata/skills/` for dynamic tool and workflow discovery.

---

## 🚀 Installation & Setup

### 1. Clone & Install
```bash
git clone https://github.com/locdata/locdata-code.git
cd locdata-code

# Install using uv or pip
uv pip install -e .
```

This registers the CLI binaries:
- `loccode`
- `locdata-code`

### 2. Configure Credentials
Add your preferred API key to `.env` or set it in your environment:
```bash
# SenseNova
export SENSENOVA_API_KEY="your_key_here"

# OR Anthropic Claude
export ANTHROPIC_API_KEY="your_key_here"

# OR OpenAI
export OPENAI_API_KEY="your_key_here"

# OR Google Gemini
export GOOGLE_API_KEY="your_key_here"
```

---

## 💻 Usage Guide

### 1. Interactive Full-Screen TUI
Launch the full interactive coding interface in your project directory:
```bash
loccode
```

### 2. Simple Terminal REPL Mode
If you prefer a lightweight terminal prompt without alternate screen buffer switching:
```bash
loccode --repl
```

### 3. Headless Task Execution (for CI/CD or Scripts)
Execute a task non-interactively:
```bash
# Fix tests and exit
loccode -x "Run pytest tests/ and fix any failing assertions"

# Ingest and summarize files
loccode -x "Read pyproject.toml and print all core dependencies"

# Output structured JSON events
loccode -x "Analyze git status" --json
```

### 4. Selecting Models & Approval Modes
```bash
# Use Claude 3.7 Sonnet
loccode -m anthropic:claude-3-7-sonnet-20250219

# Use GPT-4o with autonomous bypass mode
loccode -m openai:gpt-4o -a bypass

# Use SenseNova Flash
loccode -m sensenova-6.8-flash-lite
```

---

## ⌨️ Slash Commands Catalog

Within the interactive interface, type `/` to access built-in commands:

| Command | Aliases | Description |
|---|---|---|
| `/help` | `/?` | Display all available commands and hints |
| `/clear` | `/reset` | Clear chat stream and start a fresh session thread |
| `/approval` | | Set approval mode (`prompt`, `auto`, `bypass`) |
| `/diff` | | Inspect unstaged git changes across the project |
| `/model` | | View or switch active LLM provider |
| `/auth` | `/connect` | Check API credentials status |
| `/skills` | | List active skills discovered from `SKILL.md` |
| `/mcp` | | List configured Model Context Protocol servers |
| `/exit` | `/quit`, `/q` | Exit LocData Code |

---

## 🛠️ Configuration Scopes

LocData Code resolves configuration hierarchically:
1. **CLI Flags** (`--model`, `--approval`, `--json`)
2. **Project Configuration** (`./.locdata/config.toml`)
3. **Global User Configuration** (`~/.locdata/config.toml`)
4. **Environment Variables** (`LOCDATA_MODEL`, `LOCDATA_APPROVAL`)
5. **System Defaults**

Sample `config.toml`:
```toml
approval_mode = "prompt"
enable_web_search = true

[model]
provider = "sensenova"
model = "sensenova-6.8-flash-lite"
temperature = 0.2
```

---

## 🧪 Testing

LocData Code includes a full unit and integration test suite:

```bash
uv run pytest -v
```

---

## 📦 Publishing & Building Wheels

To build distributable wheel and source packages:
```bash
uv run python -m build
# or using hatch:
hatch build
```
Distributable artifacts will be output to `dist/`.

---

## 📄 License
MIT License. Built with pride by the **LocData AI Team**.
