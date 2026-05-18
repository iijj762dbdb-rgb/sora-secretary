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
