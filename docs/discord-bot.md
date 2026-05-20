# Discord Bot Design

## 方針
- スラッシュコマンド（Application Commands）を中心としたインターフェースを使用します。
- `Message Content Intent` は環境変数 `ENABLE_MESSAGE_CONTENT_INTENT=true` にてオプトイン（有効化）が可能です。個人用Discordサーバー・自分専用Botとしての利用を前提としています。
- 通常メッセージは無条件に監視・保存されることはなく、以下の `on_message` 条件を満たした場合のみ処理されます。
- Guild限定同期（Guild-specific command sync）により、即座のコマンド反映と権限管理を容易にします。
- `ALLOWED_DISCORD_USER_IDS` による厳格なアクセス制限を行い、自分（開発者）だけが利用できるようにします。許可外ユーザーからの呼び出しは ephemeral （または通常メッセージの場合は無視）で拒否します。

### on_message の処理条件
通常メッセージでBotが反応する条件は以下の通りです：
1. **Bot / 他のBotの無視**: Bot自身および他Botからのメッセージは無視します。
2. **ユーザー制限**: `ALLOWED_DISCORD_USER_IDS` に含まれないユーザーからのメッセージは無視します。
3. **チャンネル制限**: `MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS` が設定されている場合、そのリストに含まれるチャンネルIDのみに反応します（空の場合は全チャンネルを許可）。
   * **将来的な方針**: 現在は自分専用サーバー前提で全チャンネルまたは広いチャンネルでprefixなし対話を行えますが、将来の誤爆低減のため `MESSAGE_CONTENT_FREE_CHAT_CHANNEL_IDS` のような専用雑談チャンネルID群にのみprefixなし反応を制限する運用への移行を検討しています。
4. **Prefix / Mention 限定**: 設定された prefix（デフォルト `sora:`）またはBotへのメンションで始まるメッセージのみに反応します。**なお、環境変数で `MESSAGE_CONTENT_PREFIX=` と空に設定した場合は、prefixなしのすべての通常メッセージに反応させることができます（`MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS` で対象のチャンネルを限定する運用と併用することで、特定のチャンネル内でのprefixなしの自然な対話を実現できます）。**
5. **本文上限**: prefix/mentionを除いた本文が空の場合は無視し、4000文字を超える場合は警告を返して終了します。
6. **明示保存のみ**: 通常会話をすべて自動でデータベースに記憶することはありません。「覚えて」「記憶して」「メモして」「保存して」など、ユーザーが明示的に保存を要求した場合のみ記憶に保存されます。



## 初期コマンド
- `/ask`: Ollama を用いてLLMに質問する。通常会話用として `CHAT_MODEL` を使います。
- `/chat`: 自然文から意図を解釈し、記憶・検索・会話等へルーティングする（必要に応じて半自律的に記憶候補を提示する。また、読み取り専用操作は自然文から直接実行します）。通常会話は `CHAT_MODEL`、日報系は `SUMMARY_MODEL` を使います。
- `/remember`: 情報を記憶に保存する
- `/search`: 記憶を検索する
- `/show_memory`: 指定した記憶の詳細を表示する
- `/recent_memories`: 最近の記憶を表示する
- `/forget`: 記憶を無効化する
- `/daily`: 作業メモを日報形式に整理して表示（・保存）する。要約・整理用途として `SUMMARY_MODEL` を使います。
- `/export_memory`: 記憶をMarkdownに出力する
- `/status`: システム・Bot・Ollama・データベース・Git等の稼働状態を一覧表示（read-only）。用途別モデル設定とOllama上の存在確認も表示します。
- `/memory_lint`: 記憶DBのデータ品質、空タグ、重複タイトル、長期保存データを点検（read-only）

## /chat の自然文直接実行（Read-only 派生出力）
会話体験向上のため、安全な読み取り専用操作については自然文から直接相当コマンドを呼び出します：
1. **最近の記憶表示**: 「最近の記憶を見せて」「最新の記憶を5件」などの発言で、`/recent_memories` 相当を直接実行して表示します。（数字抽出による件数指定に対応、デフォルト10件、1〜20件）
2. **記憶の詳細表示**: 「記憶 mem_xxx を表示」「mem_xxx の中身を教えて」などの発言で、`/show_memory` 相当を直接実行して表示します。（ID指定がない場合は使い方の案内を行います）
3. **Markdownエクスポート**: 「最近の記憶をMarkdownにして」「記憶を10件エクスポートして」などの発言で、`/export_memory` 相当を直接実行し、ローカルのMarkdownファイルへエクスポートします。（数字抽出による件数指定に対応、デフォルト20件、1〜100件）

※ DB更新や削除を伴う `forget` / `delete` 系操作については、安全のため自然文からは直接実行せず、候補提示と `/forget` コマンド案内のみを行います。

## Message Context Menu (メッセージコンテキストメニュー)
ユーザーが特定のメッセージを右クリック（または長押し）して呼び出せるアプリコマンドです。`Message Content Intent` は使用せず、ユーザーが明示的に選択したメッセージのみを安全に取得して動作します：
1. **「記憶する」**: 選択したメッセージ本文を `/remember` 相当の挙動で `assistant_memory.db` に明示保存します。
   - `title`: メッセージ本文の先頭30文字程度
   - `memory_type`: `conversation_note`
   - `sensitivity`: `normal`
   - 保存完了後、新しく発行された `memory_id` とタイトルを ephemeral 応答します。
2. **「日報にする」**: 選択したメッセージ本文を Ollama にて `SUMMARY_MODEL` で日報形式に自動整理し、`daily_report` として `assistant_memory.db` に保存します。
3. **「要約する」**: 選択したメッセージ本文を Ollama にて `SUMMARY_MODEL` で短縮要約し、結果を ephemeral 応答します（データベースへの保存は行いません）。

## モデル利用
初期の最小実装では、完全自動ルーティングではなく用途別環境変数を使います。

- `CHAT_MODEL`: `/ask` と通常 `/chat`
- `SUMMARY_MODEL`: `/daily`、`/chat` 日報系、Context Menu「日報にする」「要約する」
- `CODE_MODEL`: まず `/status` 表示のみ

## 将来候補
- `/prompt`: 他LLM向けプロンプトの作成
- `/code`: コード相談やログ読解用に `CODE_MODEL` を利用する入口

