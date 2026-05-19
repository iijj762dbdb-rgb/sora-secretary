# Architecture

## 構成要素
1. **Discord Bot (Python)**
   - ユーザーとのインターフェース
   - スラッシュコマンドによる対話制御
2. **Ollama**
   - ローカルLLMエンジン (gemma3:4b など)
3. **assistant_memory.db**
   - SORA Secretary 専用の記憶DB (SQLite)
4. **Markdown Memory (将来予定)**
   - 記憶のMarkdown出力によるバックアップや連携

## Document Inbox との連携について
- 将来的には Document Inbox への **read-only連携** を計画しています。
- **初期版では Inbox の `app.db` には一切接続しません。**

## 状態管理と監視 (status_info)
- **`/status` コマンド**: システム管理やメンテナンス用として、Bot自身、ローカルOllama、記憶データベース、Gitリポジトリの状態、および SORA 上の自動デプロイログのステータスを読み取り専用 (read-only) で集約して取得するモジュール (`status_info.py`) を備えています。この監視処理はデータベースの更新やシステム破壊的な操作を一切行わないように安全に隔離されて実行されます。

