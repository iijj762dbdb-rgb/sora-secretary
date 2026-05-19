# Remaining Tasks

- [x] `/remember` `/search` `/forget` コマンドの実装
- [x] 自然文入力 `/chat text` コマンドの実装（自然な会話感・read-only直接実行対応）
- [x] Markdown エクスポート機能 (`/export_memory`, `/show_memory`)
- [x] `/daily` および `/recent_memories` コマンド
- [x] 半自律的な記憶候補提示機能
- [x] 用途別モデル設定の最小反映（`CHAT_MODEL` / `SUMMARY_MODEL` / `CODE_MODEL`）
- [x] status 確認系の read-only 実装（/status コマンド・稼働ステータス一元取得）
- [x] 記憶データベースのデータ品質点検・名寄せ候補の検出機能（/memory_lint）
- [x] SORA実機で用途別モデル設定を確認する（/status、/ask、/chat、/daily、Context Menu日報/要約）
- [x] Message Content Intent の env gated 導入と on_message 処理実装
- [x] 簡易人格（落ち着いた個人秘書: SORA Secretary）の system prompt 実装
- [x] 自然文ルーティングの共通関数化（run_chat_flow）
- [ ] `/prompt` コマンド
- [ ] model routing (router agent / 自動判定)
- [ ] Document Inbox との read-only 連携 (将来フェーズ)
- [ ] マルチエージェント化
- [x] systemd user service 化による常駐化（自動pull再起動・運用ドキュメント化完了）

