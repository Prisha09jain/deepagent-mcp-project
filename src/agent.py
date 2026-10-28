"""
Builds a LangChain DeepAgent that uses MCP for tool calling.

This is the full "agent harness" version with:
  • 7 specialist sub-agents the orchestrator can delegate to via task()
  • Filesystem permissions scoped to the project directory
  • Rich system prompt with planning & delegation guidelines
  • Multi-turn memory via checkpointer
  • Built-in harness tools (ls, read_file, write_file, edit_file, grep,
    glob, execute, task) for filesystem and shell access

Sub-agents:
  1. math_specialist     — arithmetic, powers, factorials, percentages
  2. text_analyst        — word counts, text transforms, email/URL extraction
  3. notes_manager       — CRUD operations on an in-memory notes store
  4. unit_converter      — temperature, distance, weight, data sizes
  5. datetime_expert     — current time, date math, leap years
  6. data_analyst        — statistical analysis, correlation, outlier detection
  7. expression_solver   — safe math expression evaluator, quadratic solver
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import (
    create_deep_agent,
    SubAgent,
    FilesystemPermission,
)
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# ---------------------------------------------------------------------------
# MCP server configuration
# ---------------------------------------------------------------------------
MCP_SERVERS = {
    "multi_tool_server": {
        "transport": "streamable_http",
        "url": os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp"),
    },
}

# ---------------------------------------------------------------------------
# Project root — used for filesystem permission scoping
# ---------------------------------------------------------------------------
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)

# ---------------------------------------------------------------------------
# System prompt for the main orchestrator agent
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a powerful AI orchestrator powered by the DeepAgents harness.\n\n"

    "You have direct access to 35+ MCP tools AND the ability to delegate to "
    "7 specialist sub-agents via the task() tool. You also have built-in "
    "harness tools (ls, read_file, write_file, edit_file, grep, glob) and "
    "a shell (execute) for filesystem and command-line access.\n\n"

    "## Your Specialist Sub-Agents\n"
    "Delegate to them using task() when the request matches their expertise:\n"
    "  • **math_specialist** — arithmetic, powers, factorials, percentages\n"
    "  • **text_analyst** — word count, text transforms, extract emails/URLs\n"
    "  • **notes_manager** — create, list, search, update, delete notes\n"
    "  • **unit_converter** — temperature, distance, weight, bytes\n"
    "  • **datetime_expert** — current time, date calculations, leap years\n"
    "  • **data_analyst** — statistical analysis (mean, median, std dev, "
    "percentiles), Pearson correlation, outlier detection with IQR\n"
    "  • **expression_solver** — safe math expression evaluation with "
    "variables (trig, log, sqrt…), quadratic equation solver\n\n"

    "## Guidelines\n"
    "1. **Plan first** — for multi-step requests, outline your approach.\n"
    "2. **Delegate** — use task() to send work to the right sub-agent.\n"
    "3. **Use tools** — always use MCP tools for computations; never guess.\n"
    "4. **Chain results** — for multi-step problems, pass results between "
    "   tool calls or sub-agents.\n"
    "5. **Be concise** — explain your reasoning briefly, then give a clear "
    "   final answer.\n"
    "6. **Complex tasks** — for requests spanning multiple categories "
    "   (e.g. 'analyze dataset then detect outliers, then create a note'), "
    "   break the work into sub-agent calls and combine the results.\n"
)


# ---------------------------------------------------------------------------
# Sub-agent definitions
# ---------------------------------------------------------------------------
def _build_subagents(mcp_tools):
    """Create specialist sub-agent definitions with the MCP tools."""

    math_specialist: SubAgent = {
        "name": "math_specialist",
        "description": (
            "Specialist for math: addition, subtraction, multiplication, "
            "division, exponentiation, factorials, and percentage calculations. "
            "Delegate any arithmetic or numerical computation here."
        ),
        "system_prompt": (
            "You are a math specialist. Use MCP tools (add, subtract, multiply, "
            "divide, power, factorial, percentage) for ALL calculations — never "
            "do mental math.\n\n"
            "For multi-step problems, chain tool calls and show each step. "
            "Return the final numerical answer clearly."
        ),
        "tools": mcp_tools,
    }

    text_analyst: SubAgent = {
        "name": "text_analyst",
        "description": (
            "Specialist for text analysis and transformation: word counting, "
            "character frequency analysis, case conversion, slugification, "
            "text reversal, and extracting emails or URLs from text. "
            "Delegate any text processing here."
        ),
        "system_prompt": (
            "You are a text analysis specialist. Use MCP tools (word_count, "
            "char_frequency, reverse_text, to_uppercase, to_lowercase, "
            "to_title_case, slugify, extract_emails, extract_urls) for text "
            "operations.\n\n"
            "Present results clearly in a structured format. For analysis "
            "results, highlight the most interesting findings."
        ),
        "tools": mcp_tools,
    }

    notes_manager: SubAgent = {
        "name": "notes_manager",
        "description": (
            "Specialist for managing notes: creating, listing, searching, "
            "updating, and deleting notes in the in-memory store. Each note "
            "has a title, content, tags, and timestamps. Delegate any note "
            "or task management operations here."
        ),
        "system_prompt": (
            "You are a notes/task manager. Use MCP tools (create_note, "
            "list_notes, get_note, update_note, delete_note, search_notes) "
            "to manage the user's notes.\n\n"
            "When creating notes, use descriptive titles. When listing, "
            "format results neatly. Always confirm actions (created, "
            "updated, deleted) with the note details."
        ),
        "tools": mcp_tools,
    }

    unit_converter: SubAgent = {
        "name": "unit_converter",
        "description": (
            "Specialist for unit conversions: temperature (°C↔°F), distance "
            "(km↔miles), weight (kg↔pounds), and data sizes (bytes to "
            "human-readable). Delegate any conversion tasks here."
        ),
        "system_prompt": (
            "You are a unit conversion specialist. Use MCP tools "
            "(celsius_to_fahrenheit, fahrenheit_to_celsius, km_to_miles, "
            "miles_to_km, kg_to_pounds, pounds_to_kg, bytes_to_human) "
            "for all conversions.\n\n"
            "Always show both the input and output values with their units. "
            "For multiple conversions, present them in a clear list."
        ),
        "tools": mcp_tools,
    }

    datetime_expert: SubAgent = {
        "name": "datetime_expert",
        "description": (
            "Specialist for date and time operations: getting the current "
            "date/time, calculating days between dates, adding/subtracting "
            "days from dates, and checking leap years. Delegate any "
            "date/time calculations here."
        ),
        "system_prompt": (
            "You are a date/time specialist. Use MCP tools (current_datetime, "
            "days_between, add_days_to_date, is_leap_year) for all date "
            "calculations.\n\n"
            "Present dates in a human-friendly format. When calculating "
            "durations, show the result in multiple units (days, weeks, "
            "months, years) when relevant."
        ),
        "tools": mcp_tools,
    }

    data_analyst: SubAgent = {
        "name": "data_analyst",
        "description": (
            "Specialist for data analytics: comprehensive statistical analysis "
            "of datasets (mean, median, mode, std dev, variance, percentiles, "
            "skewness, histograms), Pearson correlation between two variables, "
            "and outlier detection using the IQR method. Delegate any "
            "statistical or data analysis tasks here."
        ),
        "system_prompt": (
            "You are a data analytics specialist. Use MCP tools "
            "(analyze_dataset, correlate, detect_outliers) for all "
            "statistical computations.\n\n"
            "When presenting results, highlight key findings — is the data "
            "skewed? Are there outliers? How strong is the correlation? "
            "Always provide context and interpretation, not just raw numbers."
        ),
        "tools": mcp_tools,
    }

    expression_solver: SubAgent = {
        "name": "expression_solver",
        "description": (
            "Specialist for evaluating mathematical expressions and solving "
            "equations: safe evaluation of complex math expressions with "
            "variables and functions (trig, log, sqrt, etc.), and solving "
            "quadratic equations with full analysis (roots, discriminant, "
            "vertex, axis of symmetry). Delegate any expression evaluation "
            "or equation solving here."
        ),
        "system_prompt": (
            "You are a math expression and equation specialist. Use MCP tools "
            "(evaluate_expression, solve_quadratic) for all computations.\n\n"
            "For evaluate_expression, you can pass variables like 'x=3,y=4' "
            "and use functions like sin, cos, sqrt, log, etc.\n"
            "For quadratic equations, present the full solution including "
            "roots, discriminant analysis, vertex, and graph characteristics."
        ),
        "tools": mcp_tools,
    }

    return [
        math_specialist, text_analyst, notes_manager,
        unit_converter, datetime_expert,
        data_analyst, expression_solver,
    ]


# ---------------------------------------------------------------------------
# Filesystem permissions — scoped to project directory
# ---------------------------------------------------------------------------
FILESYSTEM_PERMISSIONS = [
    FilesystemPermission(
        operations=["read", "write"],
        paths=[PROJECT_ROOT + "/**"],
        mode="allow",
    ),
]


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------
async def build_agent(checkpointer=None):
    """Connect to MCP servers and return a fully-wired deep agent.

    The returned agent includes:
    - 35+ MCP tools across 7 categories
    - 7 specialist sub-agents accessible via task()
    - Built-in harness tools (ls, read_file, write_file, edit_file,
      grep, glob, execute, task)
    - Memory-backed checkpointer for multi-turn conversations
    """
    mcp_client = MultiServerMCPClient(MCP_SERVERS)
    tools = await mcp_client.get_tools()

    subagents = _build_subagents(tools)

    agent = create_deep_agent(
        model=os.environ.get("AGENT_MODEL", "groq:qwen/qwen3.6-27b"),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=subagents,
        permissions=FILESYSTEM_PERMISSIONS,
        checkpointer=checkpointer or InMemorySaver(),
        debug=os.environ.get("AGENT_DEBUG", "").lower() in ("1", "true"),
    )
    return agent


async def run_agent(prompt: str, thread_id: str = "1") -> str:
    """Convenience helper: builds the agent and runs a single prompt."""
    agent = await build_agent()
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content
