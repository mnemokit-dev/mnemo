"""mnemo post-install setup.

Copies the session_start hook to ~/.claude/hooks/ and registers it in
~/.claude/settings.json so Claude Code picks it up automatically.

Usage (manual):
    mnemo-setup
    python mnemo/install.py

Used by hatchling as a build hook via:
    [tool.hatch.build.hooks.custom]
    path = "mnemo/install.py"

Note: Python packaging (PEP 517/518) has no native post-install hook
mechanism. This file covers two roles:
  1. Console script (mnemo-setup) — run manually after pip install.
  2. Hatchling build hook — runs during `uv build` to remind builders.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

_CLAUDE_DIR = Path.home() / ".claude"
_HOOKS_DIR = _CLAUDE_DIR / "hooks"
_SETTINGS_PATH = _CLAUDE_DIR / "settings.json"
_THIS_DIR = Path(__file__).parent
_HOOK_SRC = _THIS_DIR / "hooks" / "session_start.py"

_MCP_SERVERS = {
    "mnemo-memory": {"command": "mnemo-memory"},
    "mnemo-connectors": {"command": "mnemo-connectors"},
    "mnemo-testing": {"command": "mnemo-testing"},
}

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _hook_command(dest: Path) -> str:
    """Build the shell command Claude Code will invoke for the hook.

    Uses sys.executable so the correct Python interpreter is picked up
    on Windows, macOS, and Linux alike.
    """
    python = sys.executable
    return f'"{python}" "{dest}"'


def _copy_hook() -> Path:
    """Copy session_start.py to ~/.claude/hooks/ and return the destination."""
    _HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _HOOKS_DIR / "session_start.py"
    shutil.copy2(_HOOK_SRC, dest)
    print(f"  Copied session_start.py → {dest}")
    return dest


def _register_hook(dest: Path) -> None:
    """Add the hook command to ~/.claude/settings.json (idempotent)."""
    data: dict = {}
    if _SETTINGS_PATH.exists():
        try:
            data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    command = _hook_command(dest)
    hooks = data.setdefault("hooks", {})
    entries: list[dict] = hooks.setdefault("UserPromptSubmit", [])

    # Idempotency: skip if session_start is already registered
    for entry in entries:
        for h in entry.get("hooks", []):
            if "session_start" in h.get("command", ""):
                print(f"  Hook already registered in {_SETTINGS_PATH}")
                return

    entries.append({"hooks": [{"type": "command", "command": command}]})
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  Hook registered in {_SETTINGS_PATH}")


def _setup_mcp(claude_json_path: Path) -> None:
    """Add mnemo MCP servers to ~/.claude.json (idempotent)."""
    data: dict = {}
    if claude_json_path.exists():
        try:
            data = json.loads(claude_json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    mcp = data.setdefault("mcpServers", {})
    added = [name for name in _MCP_SERVERS if name not in mcp]
    for name in added:
        mcp[name] = _MCP_SERVERS[name]

    if added:
        claude_json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  MCP servers added: {', '.join(added)}")
    else:
        print("  MCP servers already configured.")


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    """Run the full Claude Code setup (hooks + MCP servers)."""
    print("mnemo: setting up Claude Code integration...")

    dest = _copy_hook()
    _register_hook(dest)
    _setup_mcp(Path.home() / ".claude.json")

    print("\nDone. Restart Claude Code to activate hooks and MCP servers.")


# --------------------------------------------------------------------------- #
# Hatchling build hook (runs during `uv build` / `hatch build`)
# --------------------------------------------------------------------------- #

try:
    from hatchling.builders.hooks.plugin.interface import (
        BuildHookInterface as _BuildHookBase,
    )
except ImportError:

    class _BuildHookBase:  # type: ignore[no-redef]
        """Fallback base when hatchling is not installed."""

        def initialize(self, version: str, build_data: dict) -> None:
            pass

        def finalize(self, version: str, build_data: dict, artifact_path: str) -> None:
            pass


class CustomBuildHook(_BuildHookBase):
    """Hatchling build hook — reminds packagers to run mnemo-setup."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict) -> None:
        print(
            "mnemokit: after installing this package, run `mnemo-setup` "
            "to configure Claude Code hooks automatically."
        )

    def finalize(self, version: str, build_data: dict, artifact_path: str) -> None:
        pass


# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()
