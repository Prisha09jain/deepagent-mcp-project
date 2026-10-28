"""
Multi-purpose MCP server exposing several tool categories.

This goes well beyond simple math — the server provides tools for:
  • Math operations (add, multiply, subtract, power, factorial)
  • Text analysis (word_count, char_frequency, reverse, slugify, etc.)
  • Task / Notes manager (create, list, search, delete — in-memory store)
  • Unit conversions (temperature, distance, weight, data size)
  • Date & time utilities (current time, days between, format dates)

Run with:
    python src/mcp_server.py

Serves a streamable-HTTP MCP endpoint at http://localhost:8000/mcp
"""

import math
import re
import uuid
from datetime import datetime, timedelta
from collections import Counter

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("multi-tool-server")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. MATH TOOLS
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@mcp.tool()
def divide(a: float, b: float) -> str:
    """Divide a by b. Returns an error message if b is zero."""
    if b == 0:
        return "Error: division by zero"
    result = a / b
    return str(result) if result != int(result) else str(int(result))


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return math.pow(base, exponent)


@mcp.tool()
def factorial(n: int) -> str:
    """Compute the factorial of a non-negative integer n."""
    if n < 0:
        return "Error: factorial is not defined for negative numbers"
    if n > 170:
        return "Error: number too large (max 170)"
    return str(math.factorial(n))


@mcp.tool()
def percentage(value: float, total: float) -> str:
    """Calculate what percentage 'value' is of 'total'."""
    if total == 0:
        return "Error: total cannot be zero"
    return f"{(value / total) * 100:.2f}%"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TEXT ANALYSIS TOOLS
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def word_count(text: str) -> dict:
    """Count words, characters, sentences, and paragraphs in text."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    return {
        "characters": len(text),
        "characters_no_spaces": len(text.replace(" ", "")),
        "words": len(words),
        "sentences": len(sentences),
        "paragraphs": max(len(paragraphs), 1),
        "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 1),
    }


@mcp.tool()
def char_frequency(text: str) -> dict:
    """Analyze character frequency in text. Returns top 10 most common characters."""
    counter = Counter(text.lower())
    # Remove spaces from frequency count
    counter.pop(' ', None)
    top_10 = counter.most_common(10)
    return {char: count for char, count in top_10}


@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse the given text string."""
    return text[::-1]


@mcp.tool()
def to_uppercase(text: str) -> str:
    """Convert text to UPPERCASE."""
    return text.upper()


@mcp.tool()
def to_lowercase(text: str) -> str:
    """Convert text to lowercase."""
    return text.lower()


@mcp.tool()
def to_title_case(text: str) -> str:
    """Convert text to Title Case."""
    return text.title()


@mcp.tool()
def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug (lowercase, hyphens, no special chars)."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


@mcp.tool()
def extract_emails(text: str) -> list:
    """Extract all email addresses from the given text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


@mcp.tool()
def extract_urls(text: str) -> list:
    """Extract all URLs from the given text."""
    pattern = r'https?://[^\s<>\"\')\]]*'
    return re.findall(pattern, text)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TASK / NOTES MANAGER (in-memory store)
# ═══════════════════════════════════════════════════════════════════════════════

_notes_store: dict[str, dict] = {}


@mcp.tool()
def create_note(title: str, content: str, tags: str = "") -> dict:
    """Create a new note. Tags should be comma-separated. Returns the created note with its ID."""
    note_id = str(uuid.uuid4())[:8]
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    note = {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tag_list,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    _notes_store[note_id] = note
    return note


@mcp.tool()
def list_notes(tag_filter: str = "") -> list:
    """List all notes, optionally filtered by a tag. Returns a list of notes."""
    notes = list(_notes_store.values())
    if tag_filter:
        notes = [n for n in notes if tag_filter.lower() in [t.lower() for t in n["tags"]]]
    return notes if notes else [{"message": "No notes found"}]


@mcp.tool()
def get_note(note_id: str) -> dict:
    """Get a single note by its ID."""
    if note_id in _notes_store:
        return _notes_store[note_id]
    return {"error": f"Note '{note_id}' not found"}


@mcp.tool()
def update_note(note_id: str, title: str = "", content: str = "", tags: str = "") -> dict:
    """Update an existing note. Only provided fields are updated."""
    if note_id not in _notes_store:
        return {"error": f"Note '{note_id}' not found"}
    note = _notes_store[note_id]
    if title:
        note["title"] = title
    if content:
        note["content"] = content
    if tags:
        note["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    note["updated_at"] = datetime.now().isoformat()
    return note


@mcp.tool()
def delete_note(note_id: str) -> dict:
    """Delete a note by its ID."""
    if note_id in _notes_store:
        deleted = _notes_store.pop(note_id)
        return {"message": f"Deleted note '{deleted['title']}'", "id": note_id}
    return {"error": f"Note '{note_id}' not found"}


@mcp.tool()
def search_notes(query: str) -> list:
    """Search notes by title or content (case-insensitive)."""
    query_lower = query.lower()
    results = [
        n for n in _notes_store.values()
        if query_lower in n["title"].lower() or query_lower in n["content"].lower()
    ]
    return results if results else [{"message": f"No notes matching '{query}'"}]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. UNIT CONVERSION TOOLS
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert temperature from Celsius to Fahrenheit."""
    return round((celsius * 9 / 5) + 32, 2)


@mcp.tool()
def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert temperature from Fahrenheit to Celsius."""
    return round((fahrenheit - 32) * 5 / 9, 2)


@mcp.tool()
def km_to_miles(km: float) -> float:
    """Convert kilometers to miles."""
    return round(km * 0.621371, 4)


@mcp.tool()
def miles_to_km(miles: float) -> float:
    """Convert miles to kilometers."""
    return round(miles * 1.60934, 4)


@mcp.tool()
def kg_to_pounds(kg: float) -> float:
    """Convert kilograms to pounds."""
    return round(kg * 2.20462, 4)


@mcp.tool()
def pounds_to_kg(pounds: float) -> float:
    """Convert pounds to kilograms."""
    return round(pounds * 0.453592, 4)


@mcp.tool()
def bytes_to_human(num_bytes: float) -> str:
    """Convert bytes to human-readable format (KB, MB, GB, TB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DATE & TIME TOOLS
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def current_datetime() -> dict:
    """Get the current date and time with multiple format options."""
    now = datetime.now()
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "human": now.strftime("%B %d, %Y at %I:%M %p"),
        "day_of_week": now.strftime("%A"),
        "unix_timestamp": int(now.timestamp()),
    }


@mcp.tool()
def days_between(date1: str, date2: str) -> dict:
    """Calculate the number of days between two dates (format: YYYY-MM-DD)."""
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        delta = abs((d2 - d1).days)
        return {
            "days": delta,
            "weeks": round(delta / 7, 1),
            "months_approx": round(delta / 30.44, 1),
            "years_approx": round(delta / 365.25, 2),
        }
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}


@mcp.tool()
def add_days_to_date(date: str, days: int) -> dict:
    """Add (or subtract) days from a date. Returns the new date."""
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
        new_date = d + timedelta(days=days)
        return {
            "original_date": date,
            "days_added": days,
            "new_date": new_date.strftime("%Y-%m-%d"),
            "day_of_week": new_date.strftime("%A"),
        }
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}


@mcp.tool()
def is_leap_year(year: int) -> dict:
    """Check if a given year is a leap year."""
    leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    return {"year": year, "is_leap_year": leap}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DATA ANALYTICS TOOLS
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def analyze_dataset(numbers: str) -> dict:
    """Perform comprehensive statistical analysis on a dataset.

    Pass numbers as a comma-separated string, e.g. "10,20,30,40,50".
    Returns count, sum, mean, median, mode, std deviation, variance,
    min, max, range, percentiles (25th, 50th, 75th), skewness indicator,
    and a text-based histogram.
    """
    try:
        data = [float(x.strip()) for x in numbers.split(",") if x.strip()]
    except ValueError:
        return {"error": "Invalid input. Provide comma-separated numbers, e.g. '1,2,3,4,5'"}

    if len(data) < 2:
        return {"error": "Need at least 2 numbers for statistical analysis."}

    import statistics

    n = len(data)
    sorted_data = sorted(data)
    mean = statistics.mean(data)
    median = statistics.median(data)
    stdev = statistics.stdev(data)
    variance = statistics.variance(data)

    # Mode (handle multi-modal)
    try:
        mode = statistics.mode(data)
    except statistics.StatisticsError:
        mode = "no unique mode"

    # Percentiles via interpolation
    def percentile(d, p):
        k = (len(d) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(d) else f
        return d[f] + (k - f) * (d[c] - d[f])

    q1 = percentile(sorted_data, 25)
    q3 = percentile(sorted_data, 75)
    iqr = q3 - q1

    # Skewness indicator (Pearson's second coefficient)
    skew = 3 * (mean - median) / stdev if stdev > 0 else 0

    # Text histogram (10 bins)
    min_val, max_val = min(data), max(data)
    bin_count = min(10, n)
    bin_width = (max_val - min_val) / bin_count if max_val != min_val else 1
    bins = [0] * bin_count
    for v in data:
        idx = min(int((v - min_val) / bin_width), bin_count - 1)
        bins[idx] += 1
    max_bar = max(bins) if bins else 1
    histogram_lines = []
    for i, count in enumerate(bins):
        lo = round(min_val + i * bin_width, 2)
        hi = round(min_val + (i + 1) * bin_width, 2)
        bar = "█" * int((count / max_bar) * 20)
        histogram_lines.append(f"  [{lo:>8} – {hi:>8}] {bar} ({count})")
    histogram = "\n".join(histogram_lines)

    return {
        "count": n,
        "sum": round(sum(data), 4),
        "mean": round(mean, 4),
        "median": round(median, 4),
        "mode": mode,
        "std_deviation": round(stdev, 4),
        "variance": round(variance, 4),
        "min": min_val,
        "max": max_val,
        "range": round(max_val - min_val, 4),
        "q1_25th": round(q1, 4),
        "q3_75th": round(q3, 4),
        "iqr": round(iqr, 4),
        "skewness_pearson2": round(skew, 4),
        "skew_interpretation": (
            "approximately symmetric" if abs(skew) < 0.5
            else "moderately skewed" if abs(skew) < 1
            else "highly skewed"
        ),
        "histogram": histogram,
    }


@mcp.tool()
def correlate(x_values: str, y_values: str) -> dict:
    """Calculate Pearson correlation between two datasets.

    Both inputs are comma-separated numbers of equal length.
    Returns correlation coefficient, R², and a strength interpretation.
    """
    try:
        x = [float(v.strip()) for v in x_values.split(",") if v.strip()]
        y = [float(v.strip()) for v in y_values.split(",") if v.strip()]
    except ValueError:
        return {"error": "Invalid input. Provide comma-separated numbers."}

    if len(x) != len(y):
        return {"error": f"Datasets must be same length. Got {len(x)} and {len(y)}."}
    if len(x) < 3:
        return {"error": "Need at least 3 data points for correlation."}

    n = len(x)
    sum_x, sum_y = sum(x), sum(y)
    sum_x2 = sum(xi ** 2 for xi in x)
    sum_y2 = sum(yi ** 2 for yi in y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))

    denom = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
    if denom == 0:
        return {"error": "Cannot compute correlation — one or both variables have zero variance."}

    r = (n * sum_xy - sum_x * sum_y) / denom
    r_squared = r ** 2

    abs_r = abs(r)
    if abs_r >= 0.9:
        strength = "very strong"
    elif abs_r >= 0.7:
        strength = "strong"
    elif abs_r >= 0.5:
        strength = "moderate"
    elif abs_r >= 0.3:
        strength = "weak"
    else:
        strength = "very weak / no"

    direction = "positive" if r > 0 else "negative" if r < 0 else "none"

    return {
        "pearson_r": round(r, 6),
        "r_squared": round(r_squared, 6),
        "strength": strength,
        "direction": direction,
        "interpretation": f"{strength} {direction} correlation",
        "n": n,
    }


@mcp.tool()
def detect_outliers(numbers: str) -> dict:
    """Detect outliers in a dataset using the IQR method.

    Pass numbers as a comma-separated string.
    Returns the outliers, the IQR boundaries, and cleaned data.
    """
    try:
        data = [float(x.strip()) for x in numbers.split(",") if x.strip()]
    except ValueError:
        return {"error": "Invalid input. Provide comma-separated numbers."}

    if len(data) < 4:
        return {"error": "Need at least 4 data points for outlier detection."}

    sorted_data = sorted(data)
    n = len(sorted_data)

    def percentile(d, p):
        k = (len(d) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(d) else f
        return d[f] + (k - f) * (d[c] - d[f])

    q1 = percentile(sorted_data, 25)
    q3 = percentile(sorted_data, 75)
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    outliers = [x for x in data if x < lower_fence or x > upper_fence]
    clean = [x for x in data if lower_fence <= x <= upper_fence]

    return {
        "total_points": n,
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "lower_fence": round(lower_fence, 4),
        "upper_fence": round(upper_fence, 4),
        "outliers": outliers,
        "outlier_count": len(outliers),
        "clean_data_count": len(clean),
        "outlier_percentage": round(len(outliers) / n * 100, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SAFE EXPRESSION EVALUATOR
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def evaluate_expression(expression: str, variables: str = "") -> dict:
    """Safely evaluate a mathematical expression with optional variables.

    Supports: arithmetic (+, -, *, /, //, %, **), math functions (sin, cos,
    tan, sqrt, log, log10, exp, abs, ceil, floor, round, pi, e), and
    custom variables.

    Args:
        expression: The math expression to evaluate, e.g. "sqrt(x**2 + y**2)"
        variables: Optional comma-separated var=value pairs, e.g. "x=3,y=4"

    Returns the result along with a breakdown of what was computed.
    """
    import ast
    import operator

    # Parse variables
    var_dict = {}
    if variables.strip():
        for pair in variables.split(","):
            pair = pair.strip()
            if "=" not in pair:
                return {"error": f"Invalid variable format: '{pair}'. Use 'name=value'."}
            name, val = pair.split("=", 1)
            name = name.strip()
            try:
                var_dict[name] = float(val.strip())
            except ValueError:
                return {"error": f"Variable '{name}' has non-numeric value: '{val.strip()}'"}

    # Allowed names (safe math functions + constants)
    safe_names = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "sqrt": math.sqrt, "log": math.log, "log2": math.log2,
        "log10": math.log10, "exp": math.exp,
        "abs": abs, "ceil": math.ceil, "floor": math.floor,
        "round": round, "pow": math.pow,
        "pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
        "degrees": math.degrees, "radians": math.radians,
        "factorial": math.factorial, "gcd": math.gcd,
    }
    safe_names.update(var_dict)

    # Validate expression with AST to prevent code injection
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        return {"error": f"Syntax error in expression: {exc}"}

    # Walk the AST and ensure only safe operations
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id not in safe_names:
            return {"error": f"Unknown name '{node.id}'. Available: {', '.join(sorted(safe_names.keys()))}"}
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Attribute,
                             ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda)):
            return {"error": "Expression contains disallowed constructs."}

    try:
        # Compile and evaluate
        code = compile(tree, "<expression>", "eval")
        result = eval(code, {"__builtins__": {}}, safe_names)  # noqa: S307
    except ZeroDivisionError:
        return {"error": "Division by zero in expression."}
    except Exception as exc:
        return {"error": f"Evaluation error: {exc}"}

    return {
        "expression": expression,
        "variables": var_dict if var_dict else "none",
        "result": result,
        "result_type": type(result).__name__,
    }


@mcp.tool()
def solve_quadratic(a: float, b: float, c: float) -> dict:
    """Solve a quadratic equation ax² + bx + c = 0.

    Returns real or complex roots, discriminant, vertex, and axis of symmetry.
    """
    if a == 0:
        if b == 0:
            return {"error": "Not an equation (a=0, b=0)."}
        return {
            "equation": f"{b}x + {c} = 0",
            "type": "linear",
            "root": round(-c / b, 6),
        }

    discriminant = b ** 2 - 4 * a * c
    vertex_x = -b / (2 * a)
    vertex_y = a * vertex_x ** 2 + b * vertex_x + c

    result = {
        "equation": f"{a}x² + {b}x + {c} = 0",
        "discriminant": round(discriminant, 6),
        "vertex": {"x": round(vertex_x, 6), "y": round(vertex_y, 6)},
        "axis_of_symmetry": round(vertex_x, 6),
        "opens": "upward" if a > 0 else "downward",
    }

    if discriminant > 0:
        r1 = (-b + math.sqrt(discriminant)) / (2 * a)
        r2 = (-b - math.sqrt(discriminant)) / (2 * a)
        result["root_type"] = "two distinct real roots"
        result["roots"] = [round(r1, 6), round(r2, 6)]
    elif discriminant == 0:
        r = -b / (2 * a)
        result["root_type"] = "one repeated real root"
        result["roots"] = [round(r, 6)]
    else:
        real_part = -b / (2 * a)
        imag_part = math.sqrt(abs(discriminant)) / (2 * a)
        result["root_type"] = "two complex conjugate roots"
        result["roots"] = [
            f"{round(real_part, 6)} + {round(imag_part, 6)}i",
            f"{round(real_part, 6)} - {round(imag_part, 6)}i",
        ]

    return result


if __name__ == "__main__":
    # streamable-http transport so the agent can connect over localhost:8000/mcp
    mcp.run(transport="streamable-http")

