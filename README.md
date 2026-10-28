# DeepAgent + MCP Tool Calling

A LangChain agent built with [`deepagents`](https://github.com/langchain-ai/deepagents) (the "batteries-included agent harness") that uses the **Model Context Protocol (MCP)** for tool calling via `langchain-mcp-adapters`.

## What's in here

- `src/mcp_server.py` — a small example MCP server (math tools) built with `FastMCP`, so you have something to point the agent at out of the box. Swap this out for your own server (e.g. the Google Sheets MCP server from the internship) once you're ready.
- `src/agent.py` — builds the deep agent: connects to one or more MCP servers, pulls their tools via `MultiServerMCPClient`, and wires them into `create_deep_agent`.
- `src/main.py` — CLI entry point that runs the agent against a single prompt.
- `tests/test_agent.py` — minimal smoke test for the agent wiring.

## Setup

```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env and add your GROQ_API_KEY (or swap the model provider in src/agent.py)
```

## Running it

**Step 1 — start the example MCP server** (in one terminal):

```bash
python src/mcp_server.py
```

This starts a streamable-HTTP MCP server on `http://localhost:8000/mcp` exposing a couple of math tools (`add`, `multiply`).

**Step 2 — run the agent** (in another terminal):

```bash
python src/main.py "What is 12 times 7, then add 5 to the result?"
```

The agent will connect to the MCP server, discover its tools, and use them to answer.

## Swapping in your own MCP server

Edit the `MCP_SERVERS` config in `src/agent.py`:

```python
MCP_SERVERS = {
    "sheets": {
        "transport": "stdio",              # or "http" / "streamable_http"
        "command": "python",
        "args": ["/path/to/your/sheets_mcp_server.py"],
    },
    # add as many servers as you like — tools from all of them get merged
}
```

Any MCP-compliant server works here — stdio (local process) or HTTP (remote/long-running).

## Swapping the model

`src/agent.py` defaults to a Groq model since that's what was used during the internship project:

```python
model="groq:qwen/qwen3.6-27b"
```

Change to any [LangChain-supported provider string](https://docs.langchain.com/oss/python/langchain/models), e.g. `"openai:gpt-4.1"` or `"google_genai:gemini-2.0-flash"`.

## Project structure

```
deepagent-mcp-project/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── mcp_server.py   # example MCP server (math tools)
│   ├── agent.py         # deep agent + MCP wiring
│   └── main.py          # CLI entry point
└── tests/
    └── test_agent.py
```

## Notes / gotchas

- Never commit your `.env` file or real API keys — `.gitignore` already excludes it.
- `MultiServerMCPClient.get_tools()` opens a fresh MCP session per tool call by default. If a server needs a persistent session (stateful reads/writes), see the `langchain-mcp-adapters` docs on explicit session management.
- `deepagents` gives you planning, sub-agents, filesystem access, and context management out of the box — this scaffold only wires up the MCP tool layer on top; extend `create_deep_agent(...)` in `src/agent.py` with `sub_agents=[...]` or `system_prompt=...` as needed.
