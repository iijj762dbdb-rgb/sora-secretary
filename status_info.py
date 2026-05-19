import os
import subprocess
import httpx
from datetime import datetime
from config import ASSISTANT_MEMORY_DB, DEFAULT_MODEL, OLLAMA_BASE_URL
from assistant_memory import get_memory_stats

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
                
                has_default = False
                for name in model_names:
                    if DEFAULT_MODEL in name or name in DEFAULT_MODEL:
                        has_default = True
                        break
                
                model_str = ", ".join(model_names) if model_names else "なし"
                if has_default:
                    return f"🟢 接続成功 (モデル '{DEFAULT_MODEL}' 検出完了. 全モデル: [{model_str}])"
                else:
                    return f"⚠️ 接続成功ですがモデル '{DEFAULT_MODEL}' が未検出です (全モデル: [{model_str}])"
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
    bot_info = (
        f"**1. Bot基本情報**\n"
        f"- 状態: 🟢 Active\n"
        f"- 現在時刻: `{now_str}`\n"
        f"- 設定モデル: `{DEFAULT_MODEL}`\n"
        f"- Ollama接続先: `{OLLAMA_BASE_URL}`"
    )
    
    ollama_status = await check_ollama_status()
    ollama_info = (
        f"**2. Ollama疎通状況**\n"
        f"- 状況: {ollama_status}"
    )
    
    try:
        if os.path.exists(ASSISTANT_MEMORY_DB):
            stats = get_memory_stats()
            latest = stats.get("latest_memory")
            if latest:
                latest_str = f"`{latest['created_at']}` | `{latest['memory_type']}` | **{latest['title']}**"
            else:
                latest_str = "なし"
                
            db_info = (
                f"**3. 記憶データベース (assistant_memory.db)**\n"
                f"- パス: `{ASSISTANT_MEMORY_DB}`\n"
                f"- 存在: 🟢 あり\n"
                f"- 総記憶数: `{stats['total_count']}` 件\n"
                f"- 有効 (archived=0): `{stats['active_count']}` 件\n"
                f"- 無効 (archived=1): `{stats['archived_count']}` 件\n"
                f"- 最新の記憶: {latest_str}"
            )
        else:
            db_info = (
                f"**3. 記憶データベース (assistant_memory.db)**\n"
                f"- パス: `{ASSISTANT_MEMORY_DB}`\n"
                f"- 存在: ⚠️ なし (未作成)"
            )
    except Exception as e:
        db_info = (
            f"**3. 記憶データベース (assistant_memory.db)**\n"
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
