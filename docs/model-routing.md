# Model Routing

## 基本方針
SORAのスペック (GTX 1070 Ti / VRAM 8GB) を考慮し、4B〜8Bサイズの量子化モデルを中心に活用します。

現段階では、完全な自動ルーターやマルチエージェント化は行わず、`.env` の用途別モデル設定を既存コマンドに反映する最小構成とします。

## 環境変数

```env
DEFAULT_MODEL=gemma3:4b-it-q4_K_M
CHAT_MODEL=gemma3:4b-it-q4_K_M
SUMMARY_MODEL=qwen3:8b
CODE_MODEL=qwen2.5-coder:7b
```

- `DEFAULT_MODEL`: 後方互換用。未指定時の基準モデルとして残します。
- `CHAT_MODEL`: `/ask` と通常 `/chat` の会話用途で使います。
- `SUMMARY_MODEL`: `/daily`、`/chat` 経由の日報、Context Menu「日報にする」「要約する」で使います。
- `CODE_MODEL`: まずは `/status` 表示のみです。将来 `/code` やコード相談ルーティングで利用します。

## 現在のルーティング

- `/ask` → `CHAT_MODEL`
- `/chat` 通常会話 → `CHAT_MODEL`
- `/chat` 日報系 → `SUMMARY_MODEL`
- `/daily` → `SUMMARY_MODEL`
- Context Menu「日報にする」 → `SUMMARY_MODEL`
- Context Menu「要約する」 → `SUMMARY_MODEL`
- `/status` → `DEFAULT_MODEL` / `CHAT_MODEL` / `SUMMARY_MODEL` / `CODE_MODEL` の設定値とOllama上の存在確認を表示します。

## 実装方針

既存コマンドを大きく変更しないため、初期実装では `ask_ollama()` の内部で軽い判定を行います。

- 日報プロンプトや要約プロンプトは `SUMMARY_MODEL` に切り替えます。
- それ以外で従来 `DEFAULT_MODEL` が渡されていた会話用途は `CHAT_MODEL` に切り替えます。
- 明示的に別モデルが渡された場合は、その指定を尊重します。

## 将来構想

- `/code` やコード相談用の入口を追加し、`CODE_MODEL` を実利用する。
- `router_agent` を導入し、タスクの性質に応じて自動的に最適なモデルを選択する。
- ただし、勝手な危険操作、Document Inbox連携、通常メッセージ監視は行いません。
