# Architecture

## 構成要素
1. **Discord Bot (Python)**
   - ユーザーとのインターフェース
   - スラッシュコマンドによる対話制御
2. **専用UIフロントエンド (aster-ui)**
   - React / Vite ベースの独自Web UI
   - 記憶の整理やDIB情報の可視化を担当 (モック実装済)
3. **UI API Gateway (`api_server.py`)**
   - FastAPI ベースのローカル専用 read-only HTTP API
   - `aster-ui` から `assistant_memory.db` や `status_info.py` の情報を読むための薄い接続層
   - Discord Bot とは別プロセスで動作し、`127.0.0.1:8787` での待受を想定
   - `aster-ui/dist/` が存在する場合は、同じFastAPIプロセスから静的UIも配信する
4. **Ollama**
   - ローカルLLMエンジン (gemma3:4b など)
5. **assistant_memory.db**
   - SORA Secretary 専用の記憶DB (SQLite)
6. **Markdown Memory (将来予定)**
   - 記憶のMarkdown出力によるバックアップや連携

## Document Inbox との連携について
- 将来的には Document Inbox への **read-only連携** を計画しています。
- **初期版では Inbox の `app.db` には一切接続しません。**

## 状態管理と監視 (status_info)
- **`/status` コマンド**: システム管理やメンテナンス用として、Bot自身、ローカルOllama、記憶データベース、Gitリポジトリの状態、および SORA 上の自動デプロイログのステータスを読み取り専用 (read-only) で集約して取得するモジュール (`status_info.py`) を備えています。この監視処理はデータベースの更新やシステム破壊的な操作を一切行わないように安全に隔離されて実行されます。

## UI API Gateway (UI-1)
- `api_server.py` は、`aster-ui` を実データへ段階接続するための **read-only FastAPI Gateway** です。
- UI-1 では `GET /api/health`, `GET /api/status`, `GET /api/memories/*`, `GET /api/todos`, `GET /api/reminders`, `GET /api/daily-reports` を提供します。
- soraには `node` / `npm` を入れず、Mint側で `aster-ui` をbuildして生成した `dist/` だけをsoraへ同期します。
- `aster-ui/dist/index.html` が存在する場合、`GET /` と `GET /memory` などのSPA fallbackは同じFastAPIプロセスから `index.html` を返します。API routesは従来通り `/api/...` が優先されます。
- `dist/` が存在しない場合でもAPI起動は落ちず、`GET /` はUI未配置のread-only状態メッセージを返します。
- 書き込み系 API、Chat/Ollama 実行 API、Document Inbox 連携、systemd 操作や shell 実行などの危険操作は含めません。
