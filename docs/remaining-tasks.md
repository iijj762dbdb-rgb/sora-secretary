# Remaining Tasks

## 完了したタスク
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
- [x] systemd user service 化による常駐化（自動pull再起動・運用ドキュメント化完了）

## 次期開発の優先タスク (Phase 2 / 次回開発)
- [x] **next_action / todo 最小実装**:
  * 例：「次これやるって覚えて」「今日やることまとめて」「最近止まってる作業ある？」など、対話を通じてタスクの整理・思い出し・提案を支援する。
- [x] **reminder 最小版**:
  * ユーザーの明示的なリクエストに応じて適切なタイミングでリマインドを行う。
- [x] **朝/夜サマリー**:
  * 朝や夜の決まったタイミング（またはトリガーメッセージ）で、本日の予定ややり残したことのサマリーを提示する。（※今回は自動通知ではなく手動 /briefing として実装済）
- [ ] **Kindle / 新刊 / ニュース監視**:
  * 登録した新刊情報や外部ニュースなどを定期取得し、要約して通知する。
- [x] **専用UI / PWA (モック実装完了)**:
  * Discord以外からも手軽に記憶の確認や対話ができる専用のWeb画面のモック（`aster-ui`）を実装済。
- [x] **UI用 read-only FastAPI Gateway (UI-1)**:
  * `api_server.py` を追加し、`aster-ui` から `status` / `memories` / `todos` / `reminders` / `daily reports` を読むためのローカル read-only API を実装済。
  * Discord Bot 本体とは別プロセスで動作し、`127.0.0.1:8787` bind を前提とする。
  * `aster-ui/dist/` が存在する場合は、同じFastAPI/uvicornプロセスから静的UIを配信する。soraには `node` / `npm` を入れず、Mint側でbuildした `dist/` だけを同期する。
  * 8788での一時確認では `/api/memories/recent`, `/api/memories/exportable`, `/`, `/memory`, `/assets/...` が200 OK。SSH tunnel越しのheadless Chromeで `/#/memory` を開き、Memory 2件のタイトルとpolicy badge相当の表示も確認済み。systemd反映は未実施。
- [ ] **専用UIの実データ接続 (次フェーズ)**:
  * `aster-ui` を SORA Secretary のバックエンド（まずは read-only API、その後 Ollama / 書き込み系 API）と通信させ、実際に機能するUIとして統合する。
  * 実装計画の詳細は `docs/ui-next-implementation-plan.md` を参照。
  * `StatusView` の `/api/status` 接続、および `MemoryView` の recent/search/detail 接続は完了。
  * `HomeView` / `RightPanel` の ToDo / Reminder read-only 接続も完了。
  * 次の優先は systemd反映方法の設計、`DailyView` の read-only 接続、または write API フェーズの検討。
- [x] **assistant_memory.db の長期記憶policy対応reset実行**:
  * 既存DBをバックアップ退避し、`visibility` 等のpolicy fieldsとFTS対応の新schemaにリセット済み。
  * `ai-memory-capture` からの安全な1件実importも確認済み。
  * memories read-only API は一覧で `body` を省略し、Aster UI 側で `local_only`, `private`, `secret` な記憶の `body` をデフォルト非表示（クリック展開）とする安全方針を実装済み。
- [ ] **専用UIの実データ接続 (次フェーズ)**:
  * `DailyView` の read-only 接続の実装。
  * `aster-ui` から API 経由での記憶やタスクの追加 (write path) のUI/API設計。

## 将来的な検討・構想タスク
- [ ] **MESSAGE_CONTENT_FREE_CHAT_CHANNEL_IDS の導入**:
  * prefixなし通常会話の誤爆を防ぐため、専用雑談チャンネルのみに反応を限定する設定。
- [ ] **`/prompt` コマンド**
- [ ] **model routing (router agent / 自動判定)**
- [ ] **Document Inbox との read-only 連携** (将来フェーズ)
- [ ] **マルチエージェント化**
