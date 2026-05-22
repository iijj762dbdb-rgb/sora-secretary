# UI Next Implementation Plan

## 目的
- `aster-ui` のモックUIを、既存の Discord Bot / `assistant_memory.db` / Ollama と段階的に接続し、実運用できるローカル秘書UIへ育てる。
- 既存 docs の方針に従い、**初期フェーズでは Document Inbox の実接続を行わず**、SORA Secretary 自身の機能を安全にUI化する。

## 前提
- `docs/product-spec.md` より、初期スコープは「会話」「記憶と検索」「作業整理」「プロンプト支援」であり、Document Inbox 連携は初期版対象外。
- `docs/remaining-tasks.md` より、Discord Bot 側の MVP はかなり進んでおり、次の中心課題は **`aster-ui` の実データ接続**。
- `docs/safety-policy.md` より、削除系は物理削除禁止・自然文からの危険操作禁止・read-only 優先。
- `docs/memory-design.md` より、UI で扱う中核データは `memories` / `todos` / `reminders`。`daily_report` は記憶として保存済み。

## 実装の進め方
1. **共通API層を先に作る**
   - 現在の実装は Discord コマンド中心で、`aster-ui` から呼べる HTTP API がない。
   - まず Python 側に最小のローカルAPI層を追加し、既存の DB 関数・ステータス取得・Ollama 呼び出しを再利用できる形にする。
2. **read-only 機能から接続する**
   - `/status`、記憶一覧、ToDo一覧、リマインダー一覧など、安全な表示系を先に接続する。
3. **書き込み系は明示操作を保つ**
   - 記憶保存、ToDo追加、リマインダー作成、日報保存は、Discord 側と同じく明示的な実行導線に限定する。
4. **Document Inbox は後段に分離する**
   - `DibView` はモック維持または read-only プレースホルダのまま残し、初期接続対象には含めない。

## 機能別の実装予定

### 1. UI共通基盤 / API Gateway
- 目的: `aster-ui` と Python バックエンドを接続するための共通入口を作る。
- 現在地: **UI-1 として read-only FastAPI Gateway (`api_server.py`) を追加済み**。
- 対応内容:
  - ローカル専用の HTTP API を追加する。
  - `memories` / `todos` / `reminders` / `status` / `chat` 用のエンドポイントを定義する。
  - 既存の Discord コマンド実装から、UI でも使えるサービス関数を切り出す。
  - エラーレスポンス、タイムアウト、ローディング状態の共通仕様を決める。
- 完了条件:
  - `aster-ui` からモックデータではなく API レスポンスを読める。
  - Discord 専用ロジックと業務ロジックが分離される。

#### UI-1 で今回実装した範囲
- `GET /api/health`
- `GET /api/status`
- `GET /api/memories/recent`
- `GET /api/memories/search`
- `GET /api/memories/{memory_id}`
- `GET /api/todos`
- `GET /api/reminders`
- `GET /api/daily-reports`

#### UI-1 でまだ未実装の範囲
- Chat/Ollama 実行 API
- 書き込み系 API (`remember`, `todo_add`, `remind_add`, `daily 保存` など)
- Document Inbox 接続
- 認証付きの外部公開構成

### 2. Aster Chat / 会話機能
- 対象画面: `CommandView`
- 目的: モック応答を実際の `/ask` / `/chat` 相当の会話体験に置き換える。
- 対応内容:
  - テキスト送信で Ollama に接続し、`CHAT_MODEL` ベースの返答を返す。
  - `/chat` 相当の自然文ルーティングを UI 経由でも利用できるようにする。
  - 記憶候補提示、read-only 直接実行、危険操作の抑止を Discord と同じポリシーで統一する。
  - 会話履歴の保持方針を決める。
  - 初期版では永続チャット履歴を持たず、セッション内保持に留めるかを判断する。
- 完了条件:
  - UI から自然文で質問・検索・ToDo確認ができる。
  - `docs/safety-policy.md` に反する削除系直接実行が UI からも起きない。

### 3. Memory / 記憶検索・閲覧・保存
- 対象画面: `MemoryView`, `HomeView`
- 目的: モックの Memory Stream を `assistant_memory.db` に接続する。
- 現在地: **`MemoryView` は read-only API (`/api/memories/recent`, `/api/memories/search`, `/api/memories/{id}`) へ接続済み**。recent / search / detail、loading / error / empty、refresh を実装済み。
- 対応内容:
  - 最近の記憶一覧 API を実装する。
  - 検索 API を FTS5 ベースで接続する。
  - 記憶詳細表示 API を追加する。
  - UI 上で `remember` 実行フォームまたは会話経由保存導線を用意する。
  - `forget` は自然文から直接実行せず、ID指定の明示操作だけを許可する。
  - `export_memory` は read-only 派生出力として UI からも実行可能にする。
- 完了条件:
  - グリッド/タイムラインの両方で実データ表示できる。
  - 検索、詳細、保存、エクスポートの主要導線が揃う。

### 4. Daily / Briefing / 日次整理
- 対象画面: `DailyView`
- 目的: 日報モックを、既存の `/daily` と `/briefing` に接続する。
- 対応内容:
  - 入力テキストを `SUMMARY_MODEL` で整形して日報化する API を追加する。
  - 保存時は `daily_report` として DB に保存する。
  - 過去の日報一覧は `memories` から `memory_type='daily_report'` で取得する。
  - `/briefing` 相当の「今日の状況整理」を UI でも呼べるようにする。
  - 朝/夜の自動実行は行わず、手動実行のまま維持する。
- 完了条件:
  - UI から日報作成、保存、アーカイブ閲覧、手動ブリーフィング実行ができる。

### 5. ToDo / Next Action 管理
- 対象画面: `HomeView`, `RightPanel` 付近に追加候補
- 目的: 既に実装済みの ToDo 機能を UI 上で扱えるようにする。
- 対応内容:
  - ToDo 一覧 API を接続する。
  - ToDo 追加フォームを実装する。
  - `todo` / `doing` / `done` の状態表示と完了操作を追加する。
  - 期限切れや優先度の表示ルールを決める。
  - `HomeView` の「Active Projects & Goals」を実データへ置き換える。
- 完了条件:
  - UI だけでタスクの追加、一覧、詳細、完了ができる。
  - Discord 側と同じ ID / status モデルで整合する。

### 6. Reminder / 通知管理
- 対象画面: 新規セクション追加または `HomeView` / `RightPanel` 統合
- 目的: 既存のリマインダー機能を確認・登録できるUIを用意する。
- 対応内容:
  - pending リマインダー一覧 API を接続する。
  - リマインダー登録フォームを実装する。
  - `done(sent)` / `cancelled` への状態変更操作を追加する。
  - バックグラウンド通知そのものは引き続き Bot 側で実行し、UI は管理画面として振る舞う。
- 完了条件:
  - UI からリマインダーの追加と待機中一覧確認ができる。
  - 通知実行主体が Bot であることが保たれる。

### 7. Status / 運用監視
- 対象画面: `StatusView`
- 目的: モックのシステム状態カードを `status_info.py` に接続する。
- 現在地: **`StatusView` は UI API (`GET /api/status`) へ接続済み**。loading / error 表示と refresh button を実装済み。
- 対応内容:
  - Bot 状態、Ollama、DB、Git、systemd、ログ情報を API 化する。
  - カードUIと実データの項目対応を定義する。
  - read-only 専用であることを UI 上でも明確にする。
  - 監視系は更新ボタンまたは一定間隔の自動再取得を検討する。
- 完了条件:
  - `/status` と同等の内容を UI から確認できる。
  - 障害時にどこが落ちているかを画面で判断できる。

### 8. DIB / Document Inbox プレースホルダ
- 対象画面: `DibView`
- 目的: 将来構想として残しつつ、初期版スコープ外であることを明確化する。
- 対応内容:
  - 画面上に「将来の read-only 連携予定」である旨を表示する。
  - 実データ接続は行わず、必要ならサンプル固定表示に留める。
  - `docs/product-spec.md` と `docs/architecture.md` に揃えて、現段階では `app.db` 非接続を明示する。
- 完了条件:
  - 実装対象と将来構想の境界が UI 上でも誤解なく伝わる。

### 9. 外部監視系（Kindle / 新刊 / ニュース）
- 目的: `docs/remaining-tasks.md` にある将来の定期監視機能を切り出して整理する。
- 対応内容:
  - UI 統合の完了後に別フェーズとして設計する。
  - 情報取得元、保存方針、通知頻度、要約モデルを個別に定義する。
  - 自律機能の扱いは `docs/safety-policy.md` と整合を取る。
- 完了条件:
  - UI本体の実装計画と混線せず、別フェーズとして着手判断できる。

## 推奨実装順
1. UI共通基盤 / API Gateway
2. Status
3. Memory
4. Aster Chat
5. Daily / Briefing
6. ToDo
7. Reminder
8. DIB プレースホルダ整理
9. 外部監視系の別設計

## マイルストーン案

### Phase 1: UIを実データで読む
- Status
- Memory 一覧 / 検索 / 詳細
- Daily Archive
- ToDo / Reminder の read-only 表示

### Phase 2: UIから書き込む
- Chat 送信
- remember
- daily 保存
- todo_add / todo_done
- remind_add / remind_cancel

### Phase 3: UIとして整える
- 共通エラーハンドリング
- 楽観更新や再取得導線
- モバイル表示調整
- 実データ前提の空状態・ローディング状態整備

## 補足
- 初手で React 側から直接 SQLite や Discord 実装に触れにいくのではなく、**Python 側にUI用の薄いAPI層を置く**のが最も安全。
- DIB は画面が先行しているが、docs 上はまだ対象外なので、最初の実装計画からは切り分けるのが妥当。
- 既存の Discord コマンド群を「唯一の実装」にせず、サービス層へ寄せると UI と Bot の二重保守を避けやすい。
