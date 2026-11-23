# 🛡️ Chapter 3: Backends, Sandboxing & Safety
### *How LocData Code Touches Files and Runs Commands Without Crashing Your Computer*

> 💡 **The Simple Analogy (Explain It Like I'm 12):**  
> Imagine you give a robot scissors and markers.  
> - If you tell it *"Go anywhere in the house,"* it might draw on your parent's bedroom wall or cut an electrical wire!  
> - Instead, you put the robot in a **dedicated craft room with a locked door** (the Workspace Sandbox).  
> - And before it uses superglue, it has to **raise its hand and ask you for permission** (Human-in-the-Loop Approval).

---

## 🗄️ 1. The `BackendProtocol` Abstraction

`loccode` never talks directly to raw operating system calls. Instead, it talks to a unified backend interface:

```mermaid
flowchart TD
    Agent["LocData Code Agent (`agent.py`)"] --> Protocol["BackendProtocol Interface\n(ls, read_file, write_file, edit_file, execute)"]

    Protocol --> B1["LocalShellBackend\n(Local project root directory)"]
    Protocol --> B2["SandboxBackend\n(Isolated Cloud Micro-VM: Docker, Modal, Daytona)"]
    Protocol --> B3["FilesystemBackend\n(Safe read/write without shell commands)"]
    Protocol --> B4["CompositeBackend\n(Routes different folder paths to different places)"]

    B4 -->|Path: /workspace| Disk["Local Disk"]
    B4 -->|Path: /sandbox| Cloud["Cloud Container"]
    B4 -->|Path: /memory| SQLite["Long-Term Database"]
```

---

## ✂️ 2. Precision Editing (`edit_file`) vs. Full File Hallucination

Why does `loccode` use `edit_file` instead of rewriting entire files?

```mermaid
flowchart TD
    subgraph Bad_Approach["❌ The Fragile Way: Full-File Rewrite (`write_file`)"]
        F1["500-line existing file"] --> LLM1["LLM asked to fix line 42"]
        LLM1 --> F2["LLM attempts to rewrite all 500 lines"]
        F2 --> Fail["❌ Hallucination! Accidentally deletes lines 200-300 or forgets imports."]
    end

    subgraph Good_Approach["✅ The LocData Way: Surgical Target Replacement (`edit_file`)"]
        F3["500-line existing file"] --> LLM2["LLM locates exact lines 40-45"]
        LLM2 --> Diff["target: 'return a - b'\nreplacement: 'return a + b'"]
        Diff --> Safe["✅ Exact string match replaces ONLY line 42.\nRemaining 499 lines stay 100% untouched!"]
    end
```

---

## 🚦 3. The 3-Tier Approval Safety Gatekeeper

Before any destructive command executes, `loccode` evaluates it through its safety engine:

```mermaid
flowchart TD
    Action["Tool Call Proposed:\n`execute('rm -rf test')` or `edit_file(...)`"] --> ModeCheck{"Current Approval Mode?"}

    ModeCheck -->|PROMPT| ShowDiff["Generate Colored Unified Diff / Command Preview"]
    ShowDiff --> AskUser{"Ask Engineer:\nApprove [Y/n]?"}
    AskUser -->|Approved| Exec["Execute Tool Safely"]
    AskUser -->|Rejected| Deny["Halt & Report to LLM: Action Denied"]

    ModeCheck -->|AUTO| AutoCheck{"Is action safe?\n(e.g., pytest, git status, read-only)"}
    AutoCheck -->|YES| Exec
    AutoCheck -->|NO (e.g. rm -rf, drop table, push --force)| ShowDiff

    ModeCheck -->|BYPASS| Exec
```
