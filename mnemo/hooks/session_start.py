"""Claude Code UserPromptSubmit hook: ensure CLAUDE.md has mnemo usage rules.

Invoked by Claude Code on every UserPromptSubmit event.
Checks the current project's CLAUDE.md and injects the mnemo section when missing.

Flow:
  - No CLAUDE.md  → create file with basic template + mnemo section
  - CLAUDE.md, no mnemo section → append mnemo section
  - CLAUDE.md, mnemo section already present → do nothing
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

_SECTION_MARKER = "## mnemo"

_MNEMO_SECTION = """\
## mnemo

作業開始時: search_memory("キーワード")で関連コンテキストを確認
意思決定時: save_context("decision_YYYY-MM-DD", "内容と理由")で保存
作業終了時: save_context("progress_YYYY-MM-DD", "今日やったこと・次にやること")を保存"""

_CLAUDE_MD_TEMPLATE = """\
# {project_name}

<!-- 技術スタック・プロジェクト概要を記入 -->

## コーディング規約

<!-- コーディング規約を記入 -->

{mnemo_section}
"""

# --------------------------------------------------------------------------- #
# CLAUDE.md management
# --------------------------------------------------------------------------- #


def _ensure_claude_md(cwd: Path) -> str | None:
    """Create or update CLAUDE.md to include the mnemo section.

    Returns a human-readable message if the file was modified, else None.
    """
    claude_md = cwd / "CLAUDE.md"

    if not claude_md.exists():
        content = _CLAUDE_MD_TEMPLATE.format(
            project_name=cwd.name,
            mnemo_section=_MNEMO_SECTION,
        )
        claude_md.write_text(content, encoding="utf-8")
        return f"[mnemo] Created CLAUDE.md in {cwd}"

    existing = claude_md.read_text(encoding="utf-8")
    if _SECTION_MARKER in existing:
        return None  # Already configured — nothing to do

    updated = existing.rstrip() + "\n\n" + _MNEMO_SECTION + "\n"
    claude_md.write_text(updated, encoding="utf-8")
    return f"[mnemo] Added mnemo rules to CLAUDE.md in {cwd}"


# --------------------------------------------------------------------------- #
# Hook entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    _hook_input = json.loads(sys.stdin.read() or "{}")  # noqa: F841
    cwd = Path.cwd()
    msg = _ensure_claude_md(cwd)

    result: dict = {"continue": True}
    if msg:
        result["hookSpecificOutput"] = {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": msg,
        }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
