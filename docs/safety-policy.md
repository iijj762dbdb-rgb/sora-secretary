# Safety Policy

## 危険操作の禁止
- SORA Secretary において、破壊的な操作や危険な操作は実装しません。
- ファイルの削除、復元、同期、`fsck`、`rsync --delete`、pCloud import の実行、大量の backfill 実行などは一切禁止します。
- **自然文処理における制限**: `/chat` コマンドで「消して」等の指示があった場合でも、直接削除や無効化は行わず、候補の提示と `/forget` コマンドの使用を案内するに留めます。
- **自動記憶候補提示における制限**: パスワード、トークン、`.env` ファイルの内容、秘密鍵、個人情報と思われる機密性の高い単語やデータが含まれる場合は、長期記憶候補としての検出や提示を一切行いません。また、Document Inbox や外部送信、他のデータベース接続は一切行わず、SORA Secretary 内の `assistant_memory.db` 操作の範囲内でのみ動作します。
- **エクスポートの制限**: `/export_memory` 等の出力機能は、データベースの更新や外部送信を行わない純粋なローカルへの読み取り専用(read-only)派生出力としてのみ実装します。

## Document Inbox の分離
- 初期版では、Document Inbox の環境には接続しません。
- DBの更新は、あくまで SORA Secretary 自身の `assistant_memory.db` のみに限定します。

## read-only 優先
- 将来的に Document Inbox への接続やステータス確認系機能を実装する場合も、最初は必ず **read-only** で実装し、安全性を確保します。
