"""mnemo-setup: configure Claude Code hooks and MCP servers automatically.

Run after installation:
    mnemo-setup
"""

from __future__ import annotations

import json
from pathlib import Path

_HOOK_COMMAND = "python -m mnemo.hooks.session_start"

_MCP_SERVERS = {
    "mnemo-memory": {"command": "mnemo-memory"},
    "mnemo-connectors": {"command": "mnemo-connectors"},
    "mnemo-testing": {"command": "mnemo-testing"},
}


def _setup_hook(settings_path: Path) -> None:
    """Add mnemo UserPromptSubmit hook to ~/.claude/settings.json."""
    data: dict = {}
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    hooks = data.setdefault("hooks", {})
    user_prompt_hooks: list[dict] = hooks.setdefault("UserPromptSubmit", [])

    for entry in user_prompt_hooks:
        for h in entry.get("hooks", []):
            if h.get("command") == _HOOK_COMMAND:
                print(f"  Hook already registered in {settings_path}")
                return

    user_prompt_hooks.append({"hooks": [{"type": "command", "command": _HOOK_COMMAND}]})
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Hook registered in {settings_path}")


def _setup_mcp(claude_json_path: Path) -> None:
    """Add mnemo MCP servers to ~/.claude.json for all projects."""
    data: dict = {}
    if claude_json_path.exists():
        try:
            data = json.loads(claude_json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Global mcpServers (top-level, applies to all projects)
    mcp = data.setdefault("mcpServers", {})
    added = []
    for name, config in _MCP_SERVERS.items():
        if name not in mcp:
            mcp[name] = config
            added.append(name)

    if added:
        claude_json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  MCP servers added: {', '.join(added)}")
    else:
        print("  MCP servers already configured.")


def main() -> None:
    print("mnemo setup starting...")

    claude_dir = Path.home() / ".claude"
    _setup_hook(claude_dir / "settings.json")
    _setup_mcp(Path.home() / ".claude.json")

    print("\nDone. Restart Claude Code to activate hooks and MCP servers.")


if __name__ == "__main__":
    main()
