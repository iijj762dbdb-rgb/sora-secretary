import os
import subprocess
import httpx
from datetime import datetime
from config import (
    ASSISTANT_MEMORY_DB,
    CHAT_MODEL,
    CODE_MODEL,
    DEFAULT_MODEL,
    OLLAMA_BASE_URL,
    SUMMARY_MODEL,
    ENABLE_MESSAGE_CONTENT_INTENT,
)
from assistant_memory import get_memory_stats, get_todo_stats



ROUTED_MODELS = {
    "DEFAULT_MODEL": DEFAULT_MODEL,
    "CHAT_MODEL": CHAT_MODEL,
    "SUMMARY_MODEL": SUMMARY_MODEL,
    "CODE_MODEL": CODE_MODEL,
}


def _model_exists(configured_model: str, model_names: list[str]) -> bool:
    for name in model_names:
        if configured_model in name or name in configured_model:
            return True
    return False


async def check_ollama_status() -> str:
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = []
                for m in models:
                    name = m.get("name") or m.get("model")
                    if name:
                        model_names.append(name)

                model_str = ", ".join(model_names) if model_names else "なし"
                checks = []
                for label, configured_model in ROUTED_MODELS.items():
                    mark = "🟢" if _model_exists(configured_model, model_names) else "⚠️"
                    checks.append(f"{mark} {label}=`{configured_model}`")

                return f"接続成功. モデル確認: {' / '.join(checks)}. 全モデル: [{model_str}]"
            else:
                return f"⚠️ 接続失敗 (HTTP {response.status_code})"
    except Exception as e:
        return f"⚠️ 接続失敗 ({type(e).__name__}: {e})"


def get_git_status() -> str:
    try:
        # Branch
        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3.0
        )
        branch = res_branch.stdout.strip() if res_branch.returncode == 0 else "unknown"

        # Commit hash
        res_hash = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=3.0
        )
        commit_hash = res_hash.stdout.strip() if res_hash.returncode == 0 else "unknown"

        # Working tree status
        res_status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=3.0
        )
        if res_status.returncode == 0:
            status_lines = res_status.stdout.strip()
            working_tree = "🔴 Dirty (未コミットの変更あり)" if status_lines else "🟢 Clean"
        else:
            working_tree = "unknown"

        return f"Branch: `{branch}` | Commit: `{commit_hash}` | Working Tree: {working_tree}"
    except Exception as e:
        return f"⚠️ 取得失敗 ({type(e).__name__}: {e})"


def get_update_log_status() -> str:
    log_path = "/home/okota/logs/sora-secretary-update.log"
    if not os.path.exists(log_path):
        return "⚠️ ログファイルが見つかりません (`~/logs/sora-secretary-update.log`)"

    try:
        mtime = os.path.getmtime(log_path)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last_lines = lines[-5:] if lines else []
        last_lines_str = "".join(last_lines).strip()

        return (
            f"最終更新時刻: `{mtime_str}`\n"
            f"**直近5行の出力**:\n"
            f"```\n{last_lines_str}\n```"
        )
    except Exception as e:
        return f"⚠️ 読み取り失敗 ({type(e).__name__}: {e})"


def get_systemd_status() -> str:
    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "sora-secretary.service"],
            capture_output=True, text=True, timeout=3.0
        )
        status = res.stdout.strip()
        if status == "active":
            return "🟢 Active (起動中)"
        else:
            return f"⚠️ {status}"
    except Exception as e:
        return f"⚠️ 取得失敗 ({type(e).__name__}: {e})"


async def build_status_report() -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model_info = (
        f"- DEFAULT_MODEL: `{DEFAULT_MODEL}`\n"
        f"- CHAT_MODEL: `{CHAT_MODEL}`\n"
        f"- SUMMARY_MODEL: `{SUMMARY_MODEL}`\n"
        f"- CODE_MODEL: `{CODE_MODEL}`"
    )
    bot_info = (
        f"**1. Bot基本情報**\n"
        f"- 状態: 🟢 Active\n"
        f"- 現在時刻: `{now_str}`\n"
        f"- Message Content Intent: `{'有効' if ENABLE_MESSAGE_CONTENT_INTENT else '無効'}`\n"
        f"- Ollama接続先: `{OLLAMA_BASE_URL}`\n"
        f"- 用途別モデル設定:\n{model_info}"
    )

    ollama_status = await check_ollama_status()
    ollama_info = (
        f"**2. Ollama疎通状況**\n"
        f"- 状況: {ollama_status}"
    )

    try:
        if os.path.exists(ASSISTANT_MEMORY_DB):
            stats = get_memory_stats()
            todo_stats = get_todo_stats()
            latest = stats.get("latest_memory")
            if latest:
                latest_str = f"`{latest['created_at']}` | `{latest['memory_type']}` | **{latest['title']}**"
            else:
                latest_str = "なし"

            db_info = (
                f"**3. データベース (assistant_memory.db)**\n"
                f"- パス: `{ASSISTANT_MEMORY_DB}`\n"
                f"- 存在: 🟢 あり\n"
                f"- **[Memory]** 総数: `{stats['total_count']}` / 有効: `{stats['active_count']}` / 無効: `{stats['archived_count']}`\n"
                f"- **[Memory]** 最新: {latest_str}\n"
                f"- **[ToDo]** todo: `{todo_stats.get('todo', 0)}` / doing: `{todo_stats.get('doing', 0)}` / done: `{todo_stats.get('done', 0)}`\n"
                f"- **[ToDo]** 期限切れ: `{todo_stats.get('expired', 0)}`"
            )
        else:
            db_info = (
                f"**3. データベース (assistant_memory.db)**\n"
                f"- パス: `{ASSISTANT_MEMORY_DB}`\n"
                f"- 存在: ⚠️ なし (未作成)"
            )
    except Exception as e:
        db_info = (
            f"**3. データベース (assistant_memory.db)**\n"
            f"- パス: `{ASSISTANT_MEMORY_DB}`\n"
            f"- 状況: ⚠️ 読み取り失敗 ({type(e).__name__}: {e})"
        )

    git_info = (
        f"**4. Git管理状態**\n"
        f"- 情報: {get_git_status()}"
    )

    log_info = (
        f"**5. 自動更新ログ (sora-secretary-update.log)**\n"
        f"- 状況: {get_update_log_status()}"
    )

    systemd_info = (
        f"**6. systemd サービス状態**\n"
        f"- 状態: {get_systemd_status()}"
    )

    report = (
        f"📋 **SORA Secretary システム稼働ステータス**\n\n"
        f"{bot_info}\n\n"
        f"{ollama_info}\n\n"
        f"{db_info}\n\n"
        f"{git_info}\n\n"
        f"{log_info}\n\n"
        f"{systemd_info}"
    )

    return report
