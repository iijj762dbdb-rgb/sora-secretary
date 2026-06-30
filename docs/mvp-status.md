# MVP Status

## 現在の到達点
- [x] Discord Bot 初期セットアップとSORA上の環境構築
- [x] Guild限定syncによるスラッシュコマンド表示 (`/ask`)
- [x] SORA上の Ollama (`gemma3:4b`) 呼び出しと返答取得の疎通確認
- [x] 基本的なドキュメント (docs正本) の整備
- [x] `/chat` 自然文入力からの read-only 操作（recent/show/export）の直接実行対応と応答の会話感向上
- [x] AI用入口ドキュメント `docs/ai-codex-brief.md` の追加
- [x] Discord Message Context Menu 操作（「記憶する」「日報にする」「要約する」）の実装
- [x] systemd / 自動pull再起動の運用ドキュメント化 (`docs/operations-systemd.md`)
- [x] `/status` システム監視コマンド（read-only）の実装
- [x] `/memory_lint` データベース品質点検コマンドの実装
- [x] 用途別モデル設定の最小反映（`CHAT_MODEL` / `SUMMARY_MODEL` / `CODE_MODEL`）
- [x] Message Content Intent の env gated 導入と on_message 処理実装
- [x] 簡易人格（落ち着いた個人秘書: SORA Secretary）の system prompt 実装
- [x] 自然文ルーティングの共通関数化（run_chat_flow）
- [x] 専用UIフロントエンド (`aster-ui`) のReact/Viteベースでのモック実装・コンポーネント化
- [x] `aster-ui` 向け read-only FastAPI Gateway (`api_server.py`) の最小実装（UI-1）
- [x] `aster-ui` の `StatusView` を `/api/status` に接続し、実データの read-only 表示・refresh・loading/error handling を実装
- [x] `aster-ui` の `MemoryView` を memories read-only API に接続し、recent / search / detail と loading/error/empty を実装
- [x] `aster-ui` の `HomeView` / `RightPanel` に ToDo / Reminder read-only API を接続し、active todo / pending reminder の表示と loading/error/empty を実装
- [x] Mint側でbuildした `aster-ui/dist/` をsoraへ同期し、FastAPI/uvicornから同一originで静的配信できる構成を実装
- [x] `sora-secretary-api.service` user systemd service により、API + Aster UI static delivery をSORA上の `127.0.0.1:8787` で常駐化
- [x] Mintデスクトップに Memory UI open / service restart / status 確認のlauncherを作成

## 次のステップ
- [x] `assistant_memory.db` の構築
- `/remember`, `/search`, `/forget` コマンドの実装
- 自然文入力 `/chat text` コマンドの実装
- `/daily` および `/recent_memories` コマンドの実装
- 半自律的な記憶候補提示機能の実装
- `/show_memory` および `/export_memory` コマンドの実装
- SORA実機で `/status` の用途別モデル表示、`/ask`、`/chat`、`/daily`、Context Menu「日報にする」「要約する」を確認する
- Phase 2-A: ToDo / next_action の最小実装 (todos テーブル、スラッシュコマンド、自然文ルーティング)
- Phase 2-B: reminder 最小版の実装 (reminders テーブル、バックグラウンドループ通知、スラッシュコマンド)
- Phase 2-C: Daily Briefing MVP (手動呼び出し版 /briefing)
- Phase UI-1: Web UI 向け read-only API (`/api/status`, `/api/memories/*`, `/api/todos`, `/api/reminders`, `/api/daily-reports`)
- Phase UI static delivery: soraには `node` / `npm` を入れず、Mint build済み `aster-ui/dist/` を同期してFastAPIから配信する。user systemd service の8787常駐化後、`/api/memories/recent`, `/api/memories/exportable`, `/`, `/memory` が200 OK。MintのSSH tunnel越しheadless Chromeで `/#/memory` を開き、Memory 2件のタイトルとpolicy badge相当の表示も確認済み。
- [ ] 将来の `/code` やコード相談入口で `CODE_MODEL` を実利用するか検討する
