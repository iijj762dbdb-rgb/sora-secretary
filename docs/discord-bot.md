# Discord Bot Design

## 方針
- スラッシュコマンド（Application Commands）を中心としたインターフェースを使用します。
- `Message Content Intent` は使用しません。
- 通常メッセージの監視は行いません。
- Guild限定同期（Guild-specific command sync）により、即座のコマンド反映と権限管理を容易にします。
- `ALLOWED_DISCORD_USER_IDS` による厳格なアクセス制限を行い、自分（開発者）だけが利用できるようにします。許可外ユーザーからの呼び出しは ephemeral で拒否します。

## 初期コマンド
- `/ask`: Ollama を用いてLLMに質問する
- `/chat`: 自然文から意図を解釈し、記憶・検索・会話等へルーティングする（必要に応じて半自律的に記憶候補を提示する）
- `/remember`: 情報を記憶に保存する
- `/search`: 記憶を検索する
- `/recent_memories`: 最近の記憶を表示する
- `/forget`: 記憶を無効化する
- `/daily`: 作業メモを日報形式に整理して表示（・保存）する

## 将来候補
- `/prompt`: 他LLM向けプロンプトの作成
- `/status`: システムやInboxのステータス確認
