---
title: "Claude CodeをPythonで拡張するMCPツールmnemoを作った"
emoji: "🧠"
type: "tech"
topics: ["claudecode", "mcp", "python", "ai", "llm"]
published: false
---

## はじめに：Claude Codeを使っていて感じた課題

Claude Codeはとても便利なAIエージェントですが、使い込んでいくうちに「あ、またここから説明しなきゃいけないのか」という場面が増えてきました。

たとえば——

- プロジェクトのアーキテクチャ方針を毎回説明している
- 「前回話し合った結論、覚えてる？」という問いかけをしている
- ライブラリの選定理由をセッションをまたぐたびに再入力している

Claude Codeはセッションをまたいで記憶を保持しません。`CLAUDE.md` で静的な情報は伝えられますが、会話の中で決まった動的な情報（意思決定の経緯、調査メモ、タスク状態）を渡す仕組みが必要でした。

そこで **mnemo** を作りました。

---

## mnemoとは

**mnemo** は Claude CodeなどのAIエージェントを拡張するPython製MCPツールセットです。

MCP（Model Context Protocol）はAnthropicが策定したオープンプロトコルで、AIエージェントが外部ツール・データソースを呼び出す仕組みを標準化したものです。Claude CodeはMCPサーバーをサポートしており、サードパーティのツールをシームレスに統合できます。

mnemoは現在3つのモジュールを想定しています。

| モジュール | 説明 | ライセンス |
|---|---|---|
| `memory` | エージェントの記憶・コンテキスト管理 | MIT（無料） |
| `connectors` | API連携・ウェブスクレイピング | 商用 |
| `testing` | テスト・検証の自動化 | 商用 |

まずは `memory` モジュールをMITで公開しました。

---

## memoryモジュールの使い方

`memory` モジュールはローカルのJSONファイル（`~/.mnemo/memory.json`）にテキストをキー・バリュー形式で保存します。MCPツールとして3つの操作を提供します。

### ツール一覧

| ツール | 役割 |
|---|---|
| `save_context(key, value)` | キー・バリューでテキストを保存 |
| `load_context(key)` | キーを指定して取得 |
| `search_memory(keyword)` | キーワードで部分一致検索 |

### 実際の使い方

Claude Codeのチャットから直接呼び出せます。

```
# プロジェクトの方針を記憶させる
save_context("arch_decision", "状態管理はReduxではなくZustandを使う。理由はバンドルサイズとシンプルさ")

# 後のセッションで取り出す
load_context("arch_decision")
# → "状態管理はReduxではなくZustandを使う。理由はバンドルサイズとシンプルさ"

# キーワードで横断検索
search_memory("Zustand")
# → {"arch_decision": "状態管理はReduxではなくZustandを使う。..."}
```

実際のユースケースとしては、`CLAUDE.md` に以下のように書いておくとさらに便利です。

```markdown
# CLAUDE.md

作業前に必ず以下を確認してください：
- load_context("project_goal") でゴールを確認する
- search_memory("TODO") で未完了タスクを確認する
```

こうしておくと、Claude Codeは自動的にメモリを参照してから作業を始めてくれます。

### 実装はシンプル

サーバー本体は `FastMCP` を使って約100行です。コアロジックはこんな感じ。

```python
from __future__ import annotations

import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

MEMORY_FILE = Path.home() / ".mnemo" / "memory.json"
mcp = FastMCP("mnemo-memory")


def _load() -> dict[str, str]:
    if not MEMORY_FILE.exists():
        return {}
    return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def _save(store: dict[str, str]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(
        json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
    )


@mcp.tool()
def save_context(key: str, value: str) -> str:
    """Save text in key-value format."""
    store = _load()
    store[key] = value
    _save(store)
    return f"Saved '{key}'."


@mcp.tool()
def search_memory(keyword: str) -> str:
    """Search all stored entries for a keyword (case-insensitive)."""
    store = _load()
    kw = keyword.lower()
    results = {k: v for k, v in store.items() if kw in k.lower() or kw in v.lower()}
    return json.dumps(results, ensure_ascii=False, indent=2) if results else "No results found."
```

MCP仕様に準拠したサーバーをこれだけ簡潔に書けるのがFastMCPの魅力です。

---

## インストールとClaude Codeへの登録

### インストール

```bash
pip install mnemo
# または
uv add mnemo
```

### Claude Codeへの登録

MCP設定ファイルに追記します。

**macOS / Linux**: `~/.claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mnemo-memory": {
      "command": "mnemo-memory"
    }
  }
}
```

設定後にClaude Codeを再起動すると、`save_context`・`load_context`・`search_memory` が使えるようになります。

---

## 今後の展望

### connectors モジュール（開発中）

外部APIやウェブリソースとの連携を提供します。

- GitHub Issueの取得・操作
- Notionページの読み書き
- Slackへの通知

### testing モジュール（開発中）

AIエージェントを活用したテスト・検証の自動化を提供します。

- プロンプトのリグレッションテスト
- レスポンス品質の自動評価
- スナップショットテスト

これらは商用ライセンスとして提供予定です（[Lemon Squeezy](https://lemonsqueezy.com) での販売を検討中）。MITのコア機能で試してみて、気に入ったら有料版というモデルです。

---

## おわりに

mnemoは「Claude Codeをもっと使いやすくしたい」という個人的な課題から生まれたツールです。セッションをまたいだ記憶の維持という地味な問題ですが、実際に使うとストレスがかなり減りました。

リポジトリはこちらです。フィードバックやPRをお待ちしています。

https://github.com/mnemokit-dev/mnemo

---

*MCP（Model Context Protocol）について詳しくは [公式ドキュメント](https://modelcontextprotocol.io) をご参照ください。*
