# mnemo

Python製MCPツールセット。Claude CodeなどのAIエージェントのコンテキスト管理・API連携・テスト自動化を拡張する。

## プロジェクト概要

- **ターゲット**: Claude Codeを使う開発者
- **技術スタック**: Python, MCP (Model Context Protocol)
- **販売**: Lemon Squeezy（MIT基本機能 + 商用ライセンス有料版）

## モジュール構成

```
mnemo/
├── mnemo/
│   ├── __init__.py
│   ├── memory/
│   │   ├── __init__.py
│   │   └── server.py      # MCPサーバー本体（FastMCP使用）
│   ├── connectors/        # 未実装（商用）
│   └── testing/           # 未実装（商用）
├── tests/
├── pyproject.toml
└── README.md
```

## MCPサーバーの起動

```bash
# 開発時
uv run mnemo-memory

# インストール後
mnemo-memory
```

## メモリの保存先

`~/.mnemo/memory.json`（ユーザーホームディレクトリ固定）

## 開発ルール

### コーディング規約
- Python 3.11+
- 型ヒント必須 (`from __future__ import annotations`)
- フォーマッター: `ruff format`、リンター: `ruff check`
- テスト: `pytest`

### コミットメッセージ
```
<type>: <summary>

types: feat, fix, docs, refactor, test, chore
```

### ブランチ戦略
- `main`: リリースブランチ（直接プッシュ禁止）
- `dev`: 開発ブランチ
- `feat/<name>`: 機能開発

## ライセンス構成

- **MIT**: `memory/` の基本機能
- **商用ライセンス**: `connectors/`、`testing/` および有料機能
- ライセンスチェックロジックは `mnemo/license.py` に集約する

## mnemo使用ルール

作業開始時：
- search_memory("プロジェクト名")で関連コンテキストを確認する

意思決定をしたとき：
- save_context("decision_日付", "内容と理由")で即座に保存

作業終了時：
- save_context("progress_日付", "今日やったこと・次にやること")を保存

## 重要な制約

- MCP仕様の破壊的変更に追従すること（`modelcontextprotocol` パッケージのバージョン固定を推奨）
- 有料機能のソースコードをパブリックリポジトリに含めない
- APIキー・シークレットは `.env` で管理し、コードにハードコードしない
