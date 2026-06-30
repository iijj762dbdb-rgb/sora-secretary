# Systemd and Auto-Pull Operations

SORA Secretary が SORA 上で常駐動作し、GitHub へのプッシュを契機に自動更新・再起動される運用の詳細です。

---

## 1. 役割分担
- **開発マシン（ノートPC等）**:
  - コードの編集、テスト、リファクタリング。
  - ドキュメント（docs正本）の整備。
  - `git commit` および `git push`（`origin/main` へのプッシュ）。
- **SORA（実行環境サーバー）**:
  - Bot の実行環境、ローカル Ollama (`gemma3:4b`) の稼働。
  - 秘密情報（`.env`）、本番DB（`assistant_memory.db`）の保持。
  - リポジトリの自動更新（`git pull`）、コンパイルチェック、自動サービス再起動。

---

## 2. systemd user service (`sora-secretary.service`)
Bot 本体をデーモンプロセスとして管理し、クラッシュ時の自動復旧（自己修復）やサーバー起動時の自動起動を保証します。

- **サービス定義の目的**:
  - `sora-secretary.service` は、ユーザーセッション（`--user` 空間）で常駐し、バックグラウンド実行されます。
  - `Restart=on-failure` により、Bot がエラー終了した場合に自動で再起動します。
- **設定概要**:
  - **WorkingDirectory**: `/home/okota/code/sora-secretary`
  - **EnvironmentFile**: `/home/okota/code/sora-secretary/.env`
  - **ExecStart**: `/usr/bin/python3 bot.py`
  - **Restart**: `on-failure`
- **運用の確認・ログ確認コマンド**:
  ```bash
  # サービスのステータス確認
  systemctl --user status sora-secretary.service

  # 直近120行の起動・動作ログ確認（ノーページング）
  journalctl --user -u sora-secretary.service -n 120 --no-pager
  ```

---

## 3. Aster UI API service (`sora-secretary-api.service`)
FastAPI API と Mint build済み `aster-ui/dist/` の静的配信を、SORA上の user systemd service として常駐させます。

- **サービス定義**: `deploy/systemd/sora-secretary-api.service`
- **配置先**: `~/.config/systemd/user/sora-secretary-api.service`
- **WorkingDirectory**: `/home/okota/code/sora-secretary`
- **ExecStart**: `/home/okota/code/sora-secretary/.venv/bin/python -m uvicorn api_server:app --host 127.0.0.1 --port 8787`
- **EnvironmentFile**: なし。`.env` 内容やsecretはservice定義へ書きません。
- **Restart**: `on-failure`

運用確認:

```bash
systemd-analyze --user verify ~/.config/systemd/user/sora-secretary-api.service
systemctl --user status --no-pager -l sora-secretary-api.service
systemctl --user is-enabled sora-secretary-api.service
curl -i http://127.0.0.1:8787/api/memories/recent?limit=20
curl -i http://127.0.0.1:8787/
```

Mint側から開く場合は SSH tunnel (`127.0.0.1:8787 -> sora:127.0.0.1:8787`) を使います。`/home/okota/bin/sora-secretary-open-memory.sh` はtunnelを確認・起動し、`http://127.0.0.1:8787/#/memory` を開きます。restart/status用のdesktop launcherもMint側に配置します。

---

## 4. 自動更新スクリプト (`~/bin/update-sora-secretary.sh`)
リモート（GitHub）の最新コミットを安全に取り込み、検証した上でサービスに反映します。

- **スクリプトの目的**:
  - `origin/main` から最新コードを `git pull --ff-only` でフェッチします。
  - 依存関係（`requirements.txt`）を同期します。
  - 更新されたコードに対して `python3 -m py_compile` で構文チェックを行い、正常な場合のみ `sora-secretary.service` を再起動します（不完全なコードによる起動不能を防ぐため）。
- **主要なコマンドフロー**:
  ```bash
  cd /home/okota/code/sora-secretary
  git fetch origin main
  git pull --ff-only
  pip install -r requirements.txt
  python3 -m py_compile config.py ollama_client.py assistant_memory.py bot.py
  # コンパイル成功時のみ再起動を実行
  if [ $? -eq 0 ]; then
      systemctl --user restart sora-secretary.service
  fi
  ```
- **実行ログ出力先**:
  - `~/logs/sora-secretary-update.log`

---

## 5. 自動更新タイマー (`sora-secretary-update.timer`)
タイマー機能を用いて、上記更新スクリプトを一定間隔（例：数分おき）で定期実行します。これにより、開発マシンから `git push` するだけで自動的にデプロイが行われます。

- **タイマー定義の目的**:
  - `sora-secretary-update.timer` が定期的に `sora-secretary-update.service`（上記スクリプトをキックするサービス）を呼び出します。
- **確認コマンド**:
  ```bash
  # タイマー一覧から sora-secretary 関連を確認する
  systemctl --user list-timers | grep sora-secretary

  # タイマーの現在のステータスを確認する
  systemctl --user status sora-secretary-update.timer
  ```

---

## 6. 手動即時反映（ホットフィックス時等）
タイマーの実行を待たずに、コードの更新内容を即座に反映させたい場合のフローです。

- **実行手順**:
  ```bash
  # 手動で更新スクリプトを実行
  ~/bin/update-sora-secretary.sh

  # 更新ログを確認し、コンパイルチェックとサービス再起動が成功したか検証する
  tail -n 120 ~/logs/sora-secretary-update.log
  ```

---

## 7. 安全方針
- **SORA上での直接編集の禁止**:
  - SORAサーバー上のソースコードを直接エディタで編集することは一切禁止します。必ず開発マシンで編集・テスト・コミットしたものを push/pull するフローを厳守します。
- **ローカルの非追跡対象の保護**:
  - `.env`、`data/`（データベース）、`memory/`（エクスポート先含む）、および `logs/` ディレクトリは、`.gitignore` で除外され、git による上書きから保護されます。
- **ファストフォワードの強制**:
  - 更新は `git pull --ff-only` に限定し、意図しないコンフリクトやリモート書き換えを避けます。
- **段階的な検証デプロイ**:
  - `py_compile` が正常終了したことを判定条件としてのみ再起動を行います。
- **インフラ接続の制限**:
  - 自動更新処理や Bot 自体は、Document Inbox (`app.db`) には絶対に接続せず、完全に分離されて稼働します。

---

## 8. トラブルシューティング

| トラブル事象 | 主な原因と切り分け | 対策コマンド/解決策 |
| :--- | :--- | :--- |
| **`git pull --ff-only` が失敗する** | SORA側で不要なファイル変更がある、あるいは履歴がコンフリクトしている。 | SORA側で `git status` を確認し、`git checkout -- <file>` で競合を破棄するか、開発側と履歴を同期する。 |
| **`.env` missing または環境変数エラー** | 秘密情報ファイル `.env` が配置されていない、あるいは内容が不足している。 | SORA上の実行ディレクトリに `.env` が正しく配置されているか、中身が定義されているかを確認。 |
| **Ollamaに接続できない** | Ollamaサービスが停止している、または `OLLAMA_BASE_URL` が誤っている。 | SORA上で `systemctl status ollama` などで Ollama の稼働状況を確認する。 |
| **Discordのコマンドが一覧に出ない** | スラッシュコマンドが Discord に正常に同期（sync）されていない。 | `bot.py` 起動ログで `Slash commands synced` が表示されているかを確認する。ギルドIDの設定が正しいか `.env` を再確認。 |
| **Botが起動しない / 即時エラーで落ちる** | 依存パッケージの不足、あるいは DB ファイルのロック、コードの記述ミス。 | `journalctl --user -u sora-secretary.service -n 50` でスタックトレースを読み、構文以外の実行時エラーの原因を調査する。 |
| **自動更新ログが動いていない** | タイマーが無効化（disabled）されている、またはログの出力先フォルダが存在しない。 | `systemctl --user status sora-secretary-update.timer` を確認し、必要に応じて `enable --now` で起動する。 |

---

## 9. システム稼働状態の一元監視 (`/status`)
SORAサーバーのシェルに入ることなく、Discord上から直接安全にシステムの稼働状況を把握するための手段として、**`/status` コマンド** が実装されています。

このコマンドは以下の情報を読み取り専用で一元的に取得し、Discord に出力します：
- **Bot基本情報**: Botの稼働時刻、稼働モデル、および接続先の Ollama URL。
- **Ollama疎通**: ローカルLLMへの接続成否、設定モデルがローカルに存在するかどうか。
- **SQLite DB件数**: `assistant_memory.db` の正常性と記憶データの総数、有効な記憶数、無効化された記憶数、および最終追加日時。
- **Git管理状態**: 現在稼働しているブランチ名、コミットのショートハッシュ、およびWorking Treeがクリーンかダーティか。
- **自動デプロイログ**: SORA上の自動プル再起動ログ (`~/logs/sora-secretary-update.log`) の最終更新時刻と、最後の5行の出力。
- **systemd サービス状態**: `sora-secretary.service` および必要に応じて `sora-secretary-api.service` のアクティブ状態。

※ すべての取得処理は、不具合が発生しても Bot を停止させず、エラー原因を `Warning` としてメッセージ上に安全に内包して表示するエラーハンドリング機構を備えています。
