"""MCP server for mnemo testing module.

Provides three tools:
- validate_output    : check text output against a list of rules
- diff_check         : unified diff between expected and actual strings
- generate_test_cases: generate test case skeletons from a function description
"""

from __future__ import annotations

import difflib
import json
import textwrap

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mnemo-testing")


# ---------------------------------------------------------------------------
# Rule evaluation helpers
# ---------------------------------------------------------------------------

_RULE_TYPES = frozenset(
    ["contains", "not_contains", "min_length", "max_length", "starts_with", "ends_with", "regex"]
)


def _evaluate_rule(output: str, rule: dict) -> dict:
    """Evaluate a single rule against *output*.

    Rule schema:
        {"type": "<rule_type>", "value": "<expected>"}

    Supported types:
        contains      – output must include value
        not_contains  – output must NOT include value
        min_length    – len(output) >= int(value)
        max_length    – len(output) <= int(value)
        starts_with   – output starts with value
        ends_with     – output ends with value
        regex         – output matches regex pattern value
    """
    import re

    rule_type = rule.get("type", "")
    value = rule.get("value", "")

    if rule_type not in _RULE_TYPES:
        return {"rule": rule, "passed": False, "reason": f"Unknown rule type: '{rule_type}'"}

    try:
        if rule_type == "contains":
            passed = value in output
            reason = "" if passed else f"Expected to contain: {value!r}"
        elif rule_type == "not_contains":
            passed = value not in output
            reason = "" if passed else f"Expected NOT to contain: {value!r}"
        elif rule_type == "min_length":
            threshold = int(value)
            passed = len(output) >= threshold
            reason = "" if passed else f"Length {len(output)} < min {threshold}"
        elif rule_type == "max_length":
            threshold = int(value)
            passed = len(output) <= threshold
            reason = "" if passed else f"Length {len(output)} > max {threshold}"
        elif rule_type == "starts_with":
            passed = output.startswith(value)
            reason = "" if passed else f"Expected to start with: {value!r}"
        elif rule_type == "ends_with":
            passed = output.endswith(value)
            reason = "" if passed else f"Expected to end with: {value!r}"
        elif rule_type == "regex":
            passed = bool(re.search(value, output))
            reason = "" if passed else f"Regex did not match: {value!r}"
        else:
            passed, reason = False, "Unhandled rule type"
    except Exception as exc:
        passed, reason = False, str(exc)

    result: dict = {"rule": rule, "passed": passed}
    if not passed:
        result["reason"] = reason
    return result


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
def validate_output(output: str, rules: str) -> str:
    """Validate text output against a list of rules.

    Args:
        output: The text to validate.
        rules:  JSON array of rule objects. Each rule must have a "type" and "value".
                Supported types: contains, not_contains, min_length, max_length,
                starts_with, ends_with, regex.
                Example: '[{"type": "contains", "value": "hello"}, {"type": "min_length", "value": "10"}]'

    Returns:
        JSON object with overall pass/fail status and per-rule details.
    """
    parsed_rules: list[dict] = json.loads(rules)
    results = [_evaluate_rule(output, rule) for rule in parsed_rules]

    passed_count = sum(1 for r in results if r["passed"])
    overall = "pass" if passed_count == len(results) else "fail"

    return json.dumps(
        {
            "status": overall,
            "passed": passed_count,
            "total": len(results),
            "details": results,
        },
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def diff_check(expected: str, actual: str) -> str:
    """Compare expected and actual strings and return a unified diff.

    Args:
        expected: The expected / reference string.
        actual:   The actual output string.

    Returns:
        Unified diff as a string. Empty string if both are identical.
    """
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            expected_lines,
            actual_lines,
            fromfile="expected",
            tofile="actual",
        )
    )

    if not diff:
        return "No differences found. Outputs are identical."
    return "".join(diff)


@mcp.tool()
def generate_test_cases(function_description: str, num_cases: int = 5) -> str:
    """Generate test case skeletons from a plain-language function description.

    This tool does NOT call an LLM — it produces a structured Markdown template
    that you can fill in, covering happy paths, edge cases, and error cases.

    Args:
        function_description: Plain-language description of the function to test.
                              (e.g. "A function that reverses a string")
        num_cases:            Number of test case skeletons to generate (default 5).

    Returns:
        Markdown-formatted test case template.
    """
    num_cases = max(1, min(num_cases, 20))

    categories = [
        ("Happy path", "typical valid input"),
        ("Happy path", "another representative valid input"),
        ("Edge case", "empty input / boundary value"),
        ("Edge case", "maximum / minimum boundary"),
        ("Error case", "invalid input type or value"),
    ]

    lines = [
        f"# Test Cases: `{function_description}`",
        "",
        f"Generated {num_cases} test case skeleton(s). Fill in the blanks.",
        "",
    ]

    for i in range(num_cases):
        cat, hint = categories[i % len(categories)]
        lines += [
            f"## Case {i + 1}: {cat}",
            f"<!-- hint: {hint} -->",
            "",
            "**Description**: <!-- what this case tests -->",
            "",
            "**Input**:",
            "```",
            "# TODO: define input",
            "```",
            "",
            "**Expected output**:",
            "```",
            "# TODO: define expected output",
            "```",
            "",
            "**Notes**: <!-- edge conditions, error messages, etc. -->",
            "",
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
