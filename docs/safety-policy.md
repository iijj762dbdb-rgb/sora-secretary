# Safety Policy

## 危険操作の禁止
- SORA Secretary において、破壊的な操作や危険な操作は実装しません。
- ファイルの削除、復元、同期、`fsck`、`rsync --delete`、pCloud import の実行、大量の backfill 実行などは一切禁止します。

## Document Inbox の分離
- 初期版では、Document Inbox の環境には接続しません。
- DBの更新は、あくまで SORA Secretary 自身の `assistant_memory.db` のみに限定します。

## read-only 優先
- 将来的に Document Inbox への接続やステータス確認系機能を実装する場合も、最初は必ず **read-only** で実装し、安全性を確保します。
