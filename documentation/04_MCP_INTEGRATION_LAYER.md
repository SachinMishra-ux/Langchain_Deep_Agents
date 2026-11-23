# 🔌 Chapter 4: The MCP (Model Context Protocol) Layer
### *How LocData Code Plugs Into Any External Tool or Database in Real-Time*

> 💡 **The Simple Analogy (Explain It Like I'm 12):**  
> Think of your computer's **USB port**.  
> You can plug in a mouse, a keyboard, a microphone, or a camera. Your computer doesn't need to be redesigned every time a new USB gadget comes out—it just speaks the standard USB language.  
> **MCP (Model Context Protocol)** is the **universal USB port for AI models**! Any company can build an MCP gadget (like an SQL tool, GitHub tool, or financial calculator), and `loccode` plugs it in instantly.

---

## 🌐 The MCP Discovery & Execution Lifecycle

```mermaid
flowchart TD
    subgraph Config_Discovery["1. Configuration Discovery"]
        JSON1["Local Project: `.mcp.json`"]
        JSON2["LocData Folder: `.locdata/mcp.json`"]
        JSON3["Global Home: `~/.locdata/mcp.json`"]
        JSON1 & JSON2 & JSON3 --> MGR["`MCPManager.discover_servers()`"]
    end

    subgraph Client_Connection["2. Transport Handshake"]
        MGR --> Client["`MultiServerMCPClient`"]
        Client -->|stdio: Subprocess Pipe| S1["External Server: `my_mcp_server.py`"]
        Client -->|HTTP / SSE: Network Socket| S2["Remote Cloud MCP Server"]
    end

    subgraph Tool_Adaptation["3. Dynamic Tool Binding & Sync Adaptation"]
        S1 & S2 --> RawTools["Fetch Remote Tools (`ListToolsRequest`)\n(e.g., `calculate_roi`, `fetch_system_status`)"]
        RawTools --> Adapter["Sync/Async Tool Adapter\n(Wraps coroutine into thread-safe LangChain StructuredTool)"]
        Adapter --> AgentTools["Agent Tool Suite\n(Merged with `ls`, `grep`, `edit_file`)"]
    end

    subgraph Execution["4. Live Model Invocation"]
        AgentTools --> LLM["LLM invokes: `calculate_roi(investment=5000, revenue=18500)`"]
        LLM --> Call["`CallToolRequest` sent across stdio/SSE pipe"]
        Call --> Result["MCP Server executes and returns result string"]
        Result --> Final["Model formulates response: 'ROI is 270.00%'"]
    end
```

---

## 🛠️ How to Create an MCP Tool in 10 Lines of Python

Creating an MCP server for `loccode` requires only standard Python:

```python
# my_mcp_server.py
from mcp.server.fastmcp import FastMCP

# 1. Initialize the server
mcp = FastMCP("my_tools")

# 2. Define any custom tool using @mcp.tool()
@mcp.tool()
def check_weather(city: str) -> str:
    """Return the live weather for a city."""
    return f"The weather in {city} is sunny and 24°C."

# 3. Start the server
if __name__ == "__main__":
    mcp.run()
```

And tell `loccode` about it in `.mcp.json`:
```json
{
  "mcpServers": {
    "weather_service": {
      "command": "python3",
      "args": ["my_mcp_server.py"]
    }
  }
}
```

When you launch `loccode`, it automatically discovers `check_weather` and makes it available to the agent!
