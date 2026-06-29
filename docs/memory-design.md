# Memory Design

## assistant_memory.db の役割
- ユーザーから明示的に記憶を指示された情報（コンテキスト、アイデア、事実など）を保存するSORA Secretary専用のDBです。
- **Document Inboxの `app.db` とは完全に分離** して運用します。

## 記憶の方針
- 会話を勝手に全部保存するようなことはしません。
- ユーザーが `/remember` コマンドや、**Discord Message Context Menu（「記憶する」「日報にする」）で明示的に指定・指示した内容のみ** を保存します。自動で裏側で会話を保存することはありません。
- **半自律的な記憶候補 (Semi-autonomous memory candidate)**: 通常会話（`/chat` など）の入力や出力から、特定のキーワード（「方針」「決定」「次回」「今後」など）を検知した場合に、長期記憶に適した「記憶候補」として検出します。ただし自動で保存はせず、`/remember` コマンド用のテンプレート付きでユーザーに候補を提示し、明示的な保存操作を促します。`/daily` は例外として `daily_report` として自動保存されます。
- **ToDo管理**: `memories` テーブルとは独立した `todos` テーブルでタスク情報を管理します。物理削除は行わず、`status` (`todo`, `doing`, `done`, `archived`) で安全に状態遷移させます。
- **リマインダー管理**: `memories` や `todos` とは独立した `reminders` テーブルで通知情報を管理します。物理削除は行わず、Bot起動中のみバックグラウンドループ（1分間隔）で `due_at` を超過した pending 状態のリマインダーを通知し、通知後は `sent` または `cancelled` として保持します。自律的な外部API実行等は行いません。

## コマンド
- `/remember`: 指定した内容を記憶する
- `/show_memory`: 指定した記憶の詳細を表示する
- `/search`: 記憶から検索する
- `/recent_memories`: archived=0 の記憶を新しい順に表示する
- `/export_memory`: archived=0 の記憶を新しい順にMarkdownへ書き出す
- `/forget`: 記憶を無効化する（物理削除ではなく `archived=1`）
- `/chat`: 自然文による入力から、キーワードやIDベースで各機能（remember, search, forget候補提示, daily, 通常会話）へ振り分けます。また、安全な読み取り専用操作（recent memories, show_memory, export_memory）については、自然文から直接相当処理を実行して、ユーザーに直接結果を応答します。
- `/daily`: 作業メモをOllamaで日報形式に整理し、必要に応じて `daily_report` として保存します。
- `/memory_lint`: 記憶DBの品質や重複、古い決定事項などの改善候補を一覧表示します。


## データモデルの概念
- `memory_type`: 記憶の分類 (例: `conversation_note`, `daily_report`)
- `sensitivity`: 秘匿性 (例: `normal`)
- `archived`: 無効化フラグ (1で無効化、物理削除しない)
- `source_type`: 情報源の種別
- `version`: 将来的な版管理

## 長期記憶policy対応schema reset計画

Aster / SORA Secretary の `assistant_memory.db` はまだ本運用していないため、既存データ保持migrationではなく、DBファイルのバックアップ後に長期記憶policy対応schemaへリセットする方針を採用できます。

設計と手順は [assistant-memory-reset-schema-plan.md](assistant-memory-reset-schema-plan.md) を正本とします。実行時は必ず事前バックアップを作成し、`visibility`, `gpt_summary`, `confidence`, `review_at`, `redaction_status`, `export_allowed`, `supersedes_id`, `superseded_by_id` を含むschemaを `init_db()` とFTS triggerで一貫して作り直します。

`init_db()` はこのpolicy fields対応schemaを作成する実装に更新済みです。reset前の旧DBでも読み取り系が即時に壊れないよう、optional policy列は存在確認しながら扱います。

このresetはまだ実行しません。DB書き込み、migration、systemd変更、既存DB削除は別フェーズで、明示確認後に行います。Markdown export は、policy schema導入後は `visibility='gpt_safe'`, `export_allowed=1`, `redaction_status='sanitized'`, `sensitivity!='secret'`, `archived=0` を満たす記憶だけを出力し、raw body は出力しません。

UI/API では `/api/memories/recent`, `/api/memories/search`, `/api/memories/{memory_id}` に加え、GPT-safe export対象だけを見る `/api/memories/exportable` を提供します。
APIレスポンスの安全性および帯域最適化のため、一覧取得APIでは `body` は返さず、詳細取得APIでのみ `body` を返します。
Aster UI の Memory view では通常表示で `gpt_summary` / `summary` を優先し、`body` はread-only詳細欄に限定して表示します。
さらに、`visibility` が `local_only` または `sensitivity` が `private` / `secret` である場合は、UI上でも `body` をデフォルト非表示とし、保護警告と表示ボタンを明示的にクリックした場合のみ本文を展開する安全方針とします。

## 記憶の点検・整理方針 (Memory Lint / Review)
長期的な運用においてデータベースの健全性と検索ノイズの低減を保つため、**`/memory_lint`** コマンドが用意されています。

このコマンドは以下の観点から自動点検を行います：
- **データ品質の確保**: タグが設定されていない記憶、タイトルや本文が極端に短い（または長すぎる）記憶の検出。
- **重複の防止**: 同一タイトルの名寄せ候補の提示。
- **長期運用アラート**: `daily_report` が多すぎる場合の整理警告、長期保存された `decision` や `project_note` のリストアップと整理の推奨。

安全性のため、これらの検知は**すべて読み取り専用 (read-only)**で行われ、自動的な削除、アーカイブ化、情報の更新などの変更処理は一切発生しません。ユーザーは提示された改善候補を元に、必要に応じて手動で `/show_memory` を使って詳細を確認し、不要な場合は `/forget`（`archived=1` 化）を実行して整理します。

## 将来の構想
- OCRによる要約情報や、運用ログ要約等を参照IDつきで保存する仕組みを追加する可能性があります。
