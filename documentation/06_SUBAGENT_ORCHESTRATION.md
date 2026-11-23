# 👥 Chapter 6: Sub-Agent Spawning & Orchestration
### *How LocData Code Multiplies Its Brain Power Without Getting Confused*

> 💡 **The Simple Analogy (Explain It Like I'm 12):**  
> Imagine you are the **Lead Detective** on a big mystery case.  
> You need to:  
> 1. Check the security cameras at the bank.  
> 2. Interview the shopkeeper down the street.  
> 3. Read the financial bank statements.  
> 
> If you do all three yourself one-by-one, it takes forever, and your notebook gets full of messy scribbles.  
> Instead, you dispatch **three junior detectives (Sub-Agents)**!  
> Each junior detective goes to their location, conducts the investigation in their own notebook (Isolated Context), and comes back to your desk with a **1-page summary report**.  
> You read their 3 clean reports and instantly solve the case!

---

## 🏢 The Supervisor-Worker Orchestration Pattern

```mermaid
sequenceDiagram
    autonumber
    actor Boss as Engineer / User
    participant Supervisor as Supervisor Agent (LocData Code)
    participant Sub1 as Sub-Agent 1: Code Auditor
    participant Sub2 as Sub-Agent 2: Security Reviewer
    participant VFS as Workspace Filesystem

    Boss->>Supervisor: "Audit our website codebase for structure and bugs."
    Note over Supervisor: Supervisor creates a plan and decides to delegate!
    
    par Parallel Sub-Agent Delegation via `task` Tool
        Supervisor->>Sub1: task(description="Inspect website/index.html structure", subagent_type="code-auditor")
        Supervisor->>Sub2: task(description="Audit website/script.js for runtime bugs", subagent_type="code-auditor")
    end

    Note over Sub1,VFS: Sub-Agent 1 executes in its own isolated room
    Sub1->>VFS: read_file("website/index.html")
    Sub1->>VFS: grep("section", "website/index.html")
    Sub1-->>Supervisor: Return clean summary: "index.html has 334 lines, 5 semantic sections, 0 broken links."

    Note over Sub2,VFS: Sub-Agent 2 executes in its own isolated room
    Sub2->>VFS: read_file("website/script.js")
    Sub2->>VFS: execute("node -c website/script.js")
    Sub2-->>Supervisor: Return clean summary: "script.js has 0 syntax errors, valid event listeners, safe DOM manipulation."

    Note over Supervisor: Supervisor reads both summaries and synthesizes final answer!
    Supervisor-->>Boss: Complete, verified audit report presented cleanly!
```

---

## 🛡️ Context Isolation: Why Sub-Agents Keep the Main Brain Fast

The biggest secret to Deep Agents' subagent engine is **Context Isolation**:

```mermaid
flowchart TD
    subgraph Monolithic_Agent["❌ The Monolithic Way (Single Prompt Context)"]
        M_User["User Prompt"] --> M_Loop["Main Agent does Step 1, Step 2, ... Step 50"]
        M_Loop --> M_State["State holds 50 tool calls, 30 errors, and 100,000 tokens!"]
        M_State --> M_Crash["❌ Attention Degradation ('Lost in the Middle') & Cost Explosion"]
    end

    subgraph Deep_Agent_Subagents["✅ The Deep Agents Way (Isolated Sub-Graphs)"]
        S_User["User Prompt"] --> S_Main["Supervisor Brain"]
        S_Main -->|`task` call 1| Sub1_Graph["Sub-Graph 1 (Isolated State)\nRuns 15 turns privately"]
        S_Main -->|`task` call 2| Sub2_Graph["Sub-Graph 2 (Isolated State)\nRuns 12 turns privately"]
        
        Sub1_Graph -->|Clean 1-page summary| S_Main
        Sub2_Graph -->|Clean 1-page summary| S_Main
        
        S_Main --> S_Clean["✅ Supervisor Context stays ultra-lean (< 1,000 tokens)!\nFast, focused, and accurate."]
    end
```

---

## 🧪 Live Proof: Sub-Agent Execution in `loccode`

In our test environment (`/Users/sachinmishra/Desktop/loccode_test_env`), we executed:

```bash
loccode -x "Spin up a subagent using the task tool to inspect website/index.html and report its structure. Then summarize the result."
```

### What Happened Behind the Scenes:
1. **Tool Invocation:** The main agent invoked `task` with `subagent_type="general-purpose"`.
2. **Sub-Graph Compilation:** Deep Agents spun up a child graph with a fresh, isolated `AgentState`.
3. **Child Execution:** The child agent read `website/index.html` (334 lines), analyzed the DOM tree, counted heading tags, and checked accessibility landmarks.
4. **Result Hand-off:** The child agent returned a structured markdown summary back to the supervisor.
5. **Supervisor Synthesis:** The supervisor presented the final verified report without any of the child's raw intermediate steps cluttering the user interface.
