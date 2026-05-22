# SORA Secretary Product Specification

## 目的
SORA Secretaryは、Discord経由で利用する個人用ローカル秘書AIです。
日常のタスク管理、思考の整理、プロンプトの作成などを支援することを目的としています。

## 初期スコープ
- Discordを通じた対話インターフェース（スラッシュコマンド）
- `aster-ui` 向けのローカル read-only UI API Gateway
- Ollamaを通じたローカルLLMでの推論
- SQLite (FTS5) を用いたローカルの記憶機能
- **初期版では Document Inbox には接続しない**

## UI接続方針
- Web UI との初回接続は、Discord Bot 本体とは別プロセスの FastAPI Gateway (`api_server.py`) を介して行います。
- 初期の UI API は `127.0.0.1` bind のローカル read-only 専用とし、記憶・ToDo・リマインダー・日報・status の参照のみを提供します。
- 書き込み系 API、Chat 実行 API、Document Inbox 接続は次フェーズで検討します。

## 目指す機能
- 会話 (Ask)
- 記憶と検索 (Remember, Search, Forget)
- 作業整理 (Daily task tracking)
- Codex/Gemini向けプロンプト作成支援
