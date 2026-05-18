# Memory Design

## assistant_memory.db の役割
- ユーザーから明示的に記憶を指示された情報（コンテキスト、アイデア、事実など）を保存するSORA Secretary専用のDBです。
- **Document Inboxの `app.db` とは完全に分離** して運用します。

## 記憶の方針
- 会話を勝手に全部保存するようなことはしません。
- ユーザーが `/remember` コマンドで明示的に指示した内容のみを保存します。

## コマンド
- `/remember`: 指定した内容を記憶する
- `/search`: 記憶から検索する
- `/forget`: 記憶を無効化する（物理削除ではなく `archived=1`）
- `/chat`: 自然文による入力から、キーワード（「覚えて」「探して」等）ベースで各機能（remember, search, forget候補提示, 通常会話）へ振り分けます。

## データモデルの概念
- `memory_type`: 記憶の分類 (例: `conversation_note`)
- `sensitivity`: 秘匿性 (例: `normal`)
- `archived`: 無効化フラグ (1で無効化、物理削除しない)
- `source_type`: 情報源の種別
- `version`: 将来的な版管理

## 将来の構想
- OCRによる要約情報や、運用ログ要約等を参照IDつきで保存する仕組みを追加する可能性があります。
