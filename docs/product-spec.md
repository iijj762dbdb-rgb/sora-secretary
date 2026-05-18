# SORA Secretary Product Specification

## 目的
SORA Secretaryは、Discord経由で利用する個人用ローカル秘書AIです。
日常のタスク管理、思考の整理、プロンプトの作成などを支援することを目的としています。

## 初期スコープ
- Discordを通じた対話インターフェース（スラッシュコマンド）
- Ollamaを通じたローカルLLMでの推論
- SQLite (FTS5) を用いたローカルの記憶機能
- **初期版では Document Inbox には接続しない**

## 目指す機能
- 会話 (Ask)
- 記憶と検索 (Remember, Search, Forget)
- 作業整理 (Daily task tracking)
- Codex/Gemini向けプロンプト作成支援
