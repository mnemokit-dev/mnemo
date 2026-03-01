"""MCP server for mnemo connectors module.

Provides three tools:
- fetch_url         : fetch URL content, optionally extracting plain text
- call_api          : call an arbitrary REST API endpoint
- extract_structured: convert a webpage to LLM-friendly Markdown
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mnemo-connectors")

_TIMEOUT = 30.0
_DEFAULT_HEADERS = {"User-Agent": "mnemo-connectors/0.1"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get(url: str, headers: dict[str, str] | None = None) -> httpx.Response:
    merged = {**_DEFAULT_HEADERS, **(headers or {})}
    return httpx.get(url, headers=merged, timeout=_TIMEOUT, follow_redirects=True)


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
def fetch_url(url: str, extract_text: bool = True) -> str:
    """Fetch the content of a URL.

    Args:
        url:          The URL to fetch.
        extract_text: If True, strip HTML tags and return plain text only.
                      If False, return raw HTML.

    Returns:
        Page content as a string.
    """
    response = _get(url)
    response.raise_for_status()

    if not extract_text:
        return response.text

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


@mcp.tool()
def call_api(
    url: str,
    method: str = "GET",
    headers: str = "{}",
    body: str = "{}",
) -> str:
    """Call an arbitrary REST API endpoint.

    Args:
        url:     The API endpoint URL.
        method:  HTTP method: GET, POST, PUT, DELETE (case-insensitive).
        headers: Request headers as a JSON string (e.g. '{"Authorization": "Bearer TOKEN"}').
        body:    Request body as a JSON string (ignored for GET/DELETE).

    Returns:
        Response body as a string (JSON pretty-printed when possible).
    """
    method = method.upper()
    if method not in {"GET", "POST", "PUT", "DELETE"}:
        return f"Unsupported method: {method}"

    parsed_headers: dict[str, str] = json.loads(headers)
    parsed_body: dict[str, Any] = json.loads(body)
    merged_headers = {**_DEFAULT_HEADERS, **parsed_headers}

    with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
        if method == "GET":
            response = client.get(url, headers=merged_headers)
        elif method == "POST":
            response = client.post(url, headers=merged_headers, json=parsed_body)
        elif method == "PUT":
            response = client.put(url, headers=merged_headers, json=parsed_body)
        else:  # DELETE
            response = client.delete(url, headers=merged_headers)

    try:
        return json.dumps(response.json(), ensure_ascii=False, indent=2)
    except Exception:
        return response.text


@mcp.tool()
def extract_structured(url: str, instruction: str = "") -> str:
    """Fetch a webpage and convert it to LLM-friendly Markdown.

    Args:
        url:         The URL to fetch.
        instruction: Optional hint describing what to focus on
                     (e.g. "extract only the main article body").

    Returns:
        Page content converted to Markdown.
    """
    response = _get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "aside"]):
        tag.decompose()

    # Use <main> or <article> when available for a cleaner result
    target = soup.find("main") or soup.find("article") or soup.body or soup

    md = markdownify(str(target), heading_style="ATX", strip=["a"])
    # Collapse excessive blank lines
    import re
    md = re.sub(r"\n{3,}", "\n\n", md).strip()

    if instruction:
        return f"<!-- instruction: {instruction} -->\n\n{md}"
    return md


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
