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


## 次のステップ
- [x] `assistant_memory.db` の構築
- [x] `/remember`, `/search`, `/forget` コマンドの実装
- [x] 自然文入力 `/chat text` コマンドの実装
- [x] `/daily` および `/recent_memories` コマンドの実装
- [x] 半自律的な記憶候補提示機能の実装
- [x] `/show_memory` および `/export_memory` コマンドの実装
