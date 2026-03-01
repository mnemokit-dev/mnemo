"""MCP server for mnemo memory module.

Provides three tools:
- save_context : store a key-value pair to ~/.mnemo/memory.json
- load_context : retrieve a value by key
- search_memory: keyword search across all keys and values
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

MEMORY_FILE = Path.home() / ".mnemo" / "memory.json"

mcp = FastMCP("mnemo-memory")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load() -> dict[str, str]:
    """Return the current memory store, or an empty dict if not yet created."""
    if not MEMORY_FILE.exists():
        return {}
    return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def _save(store: dict[str, str]) -> None:
    """Persist the memory store to disk."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
def save_context(key: str, value: str) -> str:
    """Save text in key-value format.

    Args:
        key:   Identifier for the stored value (e.g. "project_goal").
        value: Text content to store.

    Returns:
        Confirmation message.
    """
    store = _load()
    store[key] = value
    _save(store)
    return f"Saved '{key}'."


@mcp.tool()
def load_context(key: str) -> str:
    """Load stored text by key.

    Args:
        key: Identifier used when saving.

    Returns:
        Stored value, or an error message if the key does not exist.
    """
    store = _load()
    if key not in store:
        return f"Key not found: '{key}'"
    return store[key]


@mcp.tool()
def search_memory(keyword: str) -> str:
    """Search all stored entries for a keyword (case-insensitive substring match).

    Args:
        keyword: Search term to match against keys and values.

    Returns:
        JSON object of matching entries, or a message if nothing is found.
    """
    store = _load()
    kw = keyword.lower()
    results = {
        k: v
        for k, v in store.items()
        if kw in k.lower() or kw in v.lower()
    }
    if not results:
        return "No results found."
    return json.dumps(results, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
