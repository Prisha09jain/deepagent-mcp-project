"""
Smoke tests for the DeepAgent + MCP multi-tool harness.

Verifies:
- All modules import cleanly
- MCP server config is well-formed
- System prompt references all sub-agents
- SubAgent definitions are valid (all 5)
- Filesystem permissions are configured
- build_agent is async
- MCP server tools are defined correctly
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_imports():
    """agent.py and mcp_server.py should import without error."""
    import agent  # noqa: F401
    import mcp_server  # noqa: F401


def test_mcp_servers_config_shape():
    """MCP_SERVERS should be a non-empty dict of transport configs."""
    from agent import MCP_SERVERS

    assert isinstance(MCP_SERVERS, dict)
    assert len(MCP_SERVERS) > 0
    for name, config in MCP_SERVERS.items():
        assert "transport" in config


def test_system_prompt_references_subagents():
    """System prompt should mention all 7 specialist sub-agents."""
    from agent import SYSTEM_PROMPT

    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0
    expected_agents = [
        "math_specialist",
        "text_analyst",
        "notes_manager",
        "unit_converter",
        "datetime_expert",
        "data_analyst",
        "expression_solver",
    ]
    for name in expected_agents:
        assert name in SYSTEM_PROMPT, f"System prompt missing sub-agent: {name}"


def test_subagent_builder_returns_seven():
    """_build_subagents should return exactly 7 SubAgent dicts."""
    from agent import _build_subagents

    subagents = _build_subagents([])
    assert isinstance(subagents, list)
    assert len(subagents) == 7

    expected_names = {
        "math_specialist",
        "text_analyst",
        "notes_manager",
        "unit_converter",
        "datetime_expert",
        "data_analyst",
        "expression_solver",
    }
    actual_names = {sa["name"] for sa in subagents}
    assert actual_names == expected_names

    for sa in subagents:
        assert "name" in sa
        assert "description" in sa
        assert "system_prompt" in sa
        assert len(sa["description"]) > 20, "Description too short"


def test_filesystem_permissions():
    """Filesystem permissions should be configured."""
    from agent import FILESYSTEM_PERMISSIONS

    assert isinstance(FILESYSTEM_PERMISSIONS, list)
    assert len(FILESYSTEM_PERMISSIONS) > 0


def test_build_agent_is_async():
    """build_agent should be an async function."""
    import asyncio
    from agent import build_agent

    assert asyncio.iscoroutinefunction(build_agent)


# ---------------------------------------------------------------------------
# MCP server tool tests (unit tests — no server needed)
# ---------------------------------------------------------------------------

def test_math_tools():
    """Math tools should compute correctly."""
    from mcp_server import add, multiply, subtract, divide, power, factorial, percentage

    assert add(2, 3) == 5
    assert multiply(4, 5) == 20
    assert subtract(10, 3) == 7
    assert divide(10, 3) == "3.3333333333333335"
    assert divide(10, 0) == "Error: division by zero"
    assert power(2, 10) == 1024
    assert factorial(5) == "120"
    assert factorial(-1) == "Error: factorial is not defined for negative numbers"
    assert percentage(25, 100) == "25.00%"


def test_text_tools():
    """Text tools should process text correctly."""
    from mcp_server import (
        word_count, reverse_text, to_uppercase, to_lowercase,
        to_title_case, slugify, extract_emails, extract_urls,
    )

    stats = word_count("Hello world. How are you?")
    assert stats["words"] == 5
    assert stats["sentences"] == 2

    assert reverse_text("hello") == "olleh"
    assert to_uppercase("hello") == "HELLO"
    assert to_lowercase("HELLO") == "hello"
    assert to_title_case("hello world") == "Hello World"
    assert slugify("Hello World! This is a Test") == "hello-world-this-is-a-test"

    emails = extract_emails("Contact us at info@example.com or support@test.org")
    assert "info@example.com" in emails
    assert "support@test.org" in emails

    urls = extract_urls("Visit https://example.com and http://test.org/page")
    assert "https://example.com" in urls


def test_notes_crud():
    """Notes CRUD operations should work correctly."""
    from mcp_server import create_note, list_notes, get_note, search_notes, delete_note, _notes_store

    # Clear any existing notes
    _notes_store.clear()

    # Create
    note = create_note("Test Note", "This is test content", "test,demo")
    assert note["title"] == "Test Note"
    assert "test" in note["tags"]
    note_id = note["id"]

    # Read
    retrieved = get_note(note_id)
    assert retrieved["title"] == "Test Note"

    # List
    notes = list_notes()
    assert len(notes) == 1

    # List with tag filter
    filtered = list_notes(tag_filter="test")
    assert len(filtered) == 1
    empty = list_notes(tag_filter="nonexistent")
    assert empty[0].get("message", "").startswith("No notes")

    # Search
    results = search_notes("test content")
    assert len(results) == 1

    # Delete
    result = delete_note(note_id)
    assert "Deleted" in result["message"]
    assert len(list_notes()) == 1  # returns "No notes found" message


def test_conversion_tools():
    """Unit conversion tools should compute correctly."""
    from mcp_server import (
        celsius_to_fahrenheit, fahrenheit_to_celsius,
        km_to_miles, miles_to_km,
        kg_to_pounds, pounds_to_kg,
        bytes_to_human,
    )

    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212
    assert fahrenheit_to_celsius(32) == 0
    assert abs(km_to_miles(1) - 0.6214) < 0.001
    assert abs(miles_to_km(1) - 1.6093) < 0.001
    assert abs(kg_to_pounds(1) - 2.2046) < 0.001
    assert abs(pounds_to_kg(1) - 0.4536) < 0.001
    assert bytes_to_human(1024) == "1.00 KB"
    assert bytes_to_human(1048576) == "1.00 MB"


def test_datetime_tools():
    """Date/time tools should work correctly."""
    from mcp_server import current_datetime, days_between, add_days_to_date, is_leap_year

    now = current_datetime()
    assert "iso" in now
    assert "date" in now
    assert "day_of_week" in now

    gap = days_between("2024-01-01", "2024-12-31")
    assert gap["days"] == 365

    future = add_days_to_date("2024-01-01", 30)
    assert future["new_date"] == "2024-01-31"

    assert is_leap_year(2024)["is_leap_year"] is True
    assert is_leap_year(2023)["is_leap_year"] is False


def test_analyze_dataset():
    """analyze_dataset should return comprehensive statistics."""
    from mcp_server import analyze_dataset

    result = analyze_dataset("10,20,30,40,50")
    assert result["count"] == 5
    assert result["mean"] == 30.0
    assert result["median"] == 30.0
    assert result["min"] == 10.0
    assert result["max"] == 50.0
    assert result["range"] == 40.0
    assert "histogram" in result
    assert "std_deviation" in result
    assert "skew_interpretation" in result

    # Error case
    err = analyze_dataset("42")
    assert "error" in err


def test_correlate():
    """correlate should compute Pearson correlation correctly."""
    from mcp_server import correlate

    # Perfect positive correlation
    result = correlate("1,2,3,4,5", "2,4,6,8,10")
    assert abs(result["pearson_r"] - 1.0) < 0.0001
    assert result["strength"] == "very strong"
    assert result["direction"] == "positive"

    # Length mismatch
    err = correlate("1,2,3", "1,2")
    assert "error" in err


def test_detect_outliers():
    """detect_outliers should find outliers using IQR method."""
    from mcp_server import detect_outliers

    result = detect_outliers("1,2,3,4,5,6,7,8,9,100")
    assert 100 in result["outliers"]
    assert result["outlier_count"] >= 1
    assert result["clean_data_count"] < result["total_points"]

    # No outliers
    result2 = detect_outliers("10,11,12,13,14,15")
    assert result2["outlier_count"] == 0


def test_evaluate_expression():
    """evaluate_expression should safely evaluate math expressions."""
    from mcp_server import evaluate_expression

    # Basic arithmetic
    result = evaluate_expression("2 + 3 * 4")
    assert result["result"] == 14

    # With variables
    result = evaluate_expression("sqrt(x**2 + y**2)", "x=3,y=4")
    assert abs(result["result"] - 5.0) < 0.0001

    # Trig
    import math
    result = evaluate_expression("sin(pi/2)")
    assert abs(result["result"] - 1.0) < 0.0001

    # Error: unknown name
    err = evaluate_expression("os.system('ls')")
    assert "error" in err


def test_solve_quadratic():
    """solve_quadratic should find roots and vertex."""
    from mcp_server import solve_quadratic

    # x^2 - 5x + 6 = 0 => roots 2 and 3
    result = solve_quadratic(1, -5, 6)
    assert result["root_type"] == "two distinct real roots"
    assert sorted(result["roots"]) == [2.0, 3.0]
    assert result["discriminant"] == 1.0

    # x^2 + 1 = 0 => complex roots
    result = solve_quadratic(1, 0, 1)
    assert result["root_type"] == "two complex conjugate roots"

    # x^2 - 4x + 4 = 0 => repeated root at 2
    result = solve_quadratic(1, -4, 4)
    assert result["root_type"] == "one repeated real root"
    assert result["roots"] == [2.0]


if __name__ == "__main__":
    test_imports()
    test_mcp_servers_config_shape()
    test_system_prompt_references_subagents()
    test_subagent_builder_returns_seven()
    test_filesystem_permissions()
    test_build_agent_is_async()
    test_math_tools()
    test_text_tools()
    test_notes_crud()
    test_conversion_tools()
    test_datetime_tools()
    test_analyze_dataset()
    test_correlate()
    test_detect_outliers()
    test_evaluate_expression()
    test_solve_quadratic()
    print("All smoke tests passed.")
