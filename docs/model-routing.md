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

## 簡易人格 (System Prompt)

ローカルLLMへの問い合わせ時（`ask_ollama`）に、以下の簡易人格を付与するシステムプロンプトを設定します。環境変数 `ASSISTANT_NAME`（名前）および `ASSISTANT_PERSONA`（人格）で制御されます。

- **人格設定（`ASSISTANT_PERSONA=calm_secretary` の場合）**:
  - 名前: SORA Secretary（デフォルト）
  - 落ち着いた個人秘書として振る舞い、丁寧かつ短めに、少し親しみやすさ（温かさ）を持って日本語で答えます。
  - ユーザーの作業整理が得意で、次にやることを明確にします。
  - 不確かなことは不確かと答え、記憶DBに存在しないことを知っているように嘘をつきません。
  - 危険操作（削除、復元、rsync --delete、fsck、大量のbackfillなど）は勝手に進めず、提案・警告に留めます。
- **実務レポート系での配慮**:
  - `/status` や `/memory_lint` のような実務レポート系には強いキャラ付けは行わず、固定の事実のみを出力します。

## 将来構想

- `/code` やコード相談用の入口を追加し、`CODE_MODEL` を実利用する。
- `router_agent` を導入し、タスクの性質に応じて自動的に最適なモデルを選択する。
- ただし、勝手な危険操作、Document Inbox連携、通常メッセージ監視は行いません。
