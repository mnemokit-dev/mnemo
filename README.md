# mnemo

Python製MCPツールセット。Claude CodeなどのAIエージェントのコンテキスト管理・API連携・テスト自動化を拡張します。

## モジュール

| モジュール | 説明 | ライセンス |
|---|---|---|
| `memory` | エージェントの記憶・コンテキスト管理 | MIT |
| `connectors` | API連携・ウェブスクレイピング | 商用 |
| `testing` | テスト・検証の自動化 | 商用 |

---

## memory モジュール

ローカルJSONファイル（`~/.mnemo/memory.json`）にキー・バリュー形式でテキストを保存します。

### ツール一覧

| ツール | 説明 |
|---|---|
| `save_context` | キー・バリュー形式でテキストを保存 |
| `load_context` | キーを指定して取得 |
| `search_memory` | キーワードで曖昧検索（部分一致・大文字小文字無視） |

### インストール

```bash
pip install mnemokit
mnemo-setup
```

`mnemo-setup` を実行すると、Claude Code の hooks と MCP サーバー設定が自動的に構成されます。

> **パッケージ名について**: PyPI の `mnemo` は 2021 年から更新のない別プロジェクトが占有しているため、`mnemokit` という名前で公開しています。

### Claude Code への登録

`mnemo-setup` が自動設定します。手動で行う場合は `~/.claude/settings.json` に以下を追記してください。

```json
{
  "mcpServers": {
    "mnemo-memory": {
      "command": "mnemo-memory"
    }
  }
}
```

### 使用例

```
# Claude Code のチャットで
save_context("project_goal", "MCPツールセットのmvpをリリースする")
load_context("project_goal")
search_memory("mvp")
```

### ローカル開発

```bash
git clone https://github.com/yourname/mnemo
cd mnemo
uv sync --extra dev
uv run pytest
```

---

## ライセンス

- `memory` モジュール: [MIT License](LICENSE)
- `connectors` / `testing` モジュール: 商用ライセンス（[Lemon Squeezy](https://lemonsqueezy.com) にて販売）
