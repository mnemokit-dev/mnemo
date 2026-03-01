"""Claude Code UserPromptSubmit hook: inject recent mnemo memory context.

Configure in ~/.claude/settings.json:
  {
    "hooks": {
      "UserPromptSubmit": [
        {"hooks": [{"type": "command", "command": "python -m mnemo.hooks.session_start"}]}
      ]
    }
  }

Or run `mnemo-setup` to configure automatically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_MEMORY_PATH = Path.home() / ".mnemo" / "memory.json"
_MAX_ENTRIES = 5


def _load_recent_memory() -> dict[str, str]:
    """Return the most recent entries from ~/.mnemo/memory.json.

    Progress and decision entries are prioritised.
    """
    if not _MEMORY_PATH.exists():
        return {}
    try:
        data: dict[str, str] = json.loads(_MEMORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

    priority = {k: v for k, v in data.items() if k.startswith(("progress_", "decision_"))}
    rest = {k: v for k, v in data.items() if k not in priority}
    merged = {**rest, **priority}
    return dict(list(merged.items())[-_MAX_ENTRIES:])


def main() -> None:
    _hook_input = json.loads(sys.stdin.read() or "{}")  # noqa: F841 – reserved for future use
    recent = _load_recent_memory()

    if not recent:
        print(json.dumps({"continue": True}))
        return

    lines = ["[mnemo: recent memory]"]
    for key, value in recent.items():
        lines.append(f"  {key}: {value}")
    context = "\n".join(lines)

    print(
        json.dumps(
            {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                },
            }
        )
    )


if __name__ == "__main__":
    main()
