import discord
from discord import app_commands
import re

from config import (
    DISCORD_BOT_TOKEN,
    ALLOWED_DISCORD_USER_IDS,
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    DISCORD_GUILD_ID_INT,
    MEMORY_DIR,
)
from ollama_client import ask_ollama
from assistant_memory import (
    init_db,
    remember_memory,
    search_memories,
    forget_memory,
    get_recent_memories,
    get_memory,
    export_memories_to_markdown,
)


class SoraSecretary(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        if DISCORD_GUILD_ID_INT:
            guild = discord.Object(id=DISCORD_GUILD_ID_INT)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {DISCORD_GUILD_ID_INT}.", flush=True)
        else:
            await self.tree.sync()
            print("Slash commands synced globally.", flush=True)

    async def on_ready(self) -> None:
        init_db()
        print("assistant_memory database initialized.", flush=True)
        print(f"Logged in as {self.user}.")


client = SoraSecretary()


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_DISCORD_USER_IDS


def split_message(text: str, limit: int = 1900) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""

    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            while len(line) > limit:
                chunks.append(line[:limit])
                line = line[limit:]
        current += line

    if current:
        chunks.append(current)

    return chunks


def is_sensitive(text: str) -> bool:
    lower_text = text.lower()
    sensitive_keywords = ["password", "token", ".env", "secret", "private key", "パスワード", "トークン", "秘密鍵", "api_key", "apikey"]
    return any(k in lower_text for k in sensitive_keywords)


def detect_memory_candidate(text: str) -> bool:
    if is_sensitive(text):
        return False
    candidate_keywords = ["方針", "決定", "次回", "今後", "覚えて", "メモ", "不採用", "禁止", "注意", "完了", "実装済み"]
    return any(k in text for k in candidate_keywords)


def extract_limit(text: str, default: int, max_value: int) -> int:
    match = re.search(r'\d+', text)
    if match:
        try:
            val = int(match.group(0))
            if val > max_value:
                return max_value
            if val < 1:
                return default
            return val
        except ValueError:
            return default
    return default


def extract_memory_id(text: str) -> str | None:
    match = re.search(r'mem_[a-zA-Z0-9_]+', text)
    if match:
        return match.group(0)
    return None


def format_recent_memories(results: list[dict]) -> str:
    lines = [f"🕒 **最近の記憶** (上位{len(results)}件):"]
    for r in results:
        lines.append(f"- **{r['title']}** (`{r['id']}`) [{r['created_at']}]\n  Tags: {r['tags']}\n  {r['summary']}...")
    return "\n".join(lines)


def format_memory_detail(mem: dict) -> str:
    lines = [
        f"📄 **記憶詳細** (`{mem['id']}`)",
        f"**Title**: {mem['title']}",
        f"**Type**: {mem['memory_type']}",
        f"**Sensitivity**: {mem['sensitivity']}",
        f"**Tags**: {mem['tags']}",
        f"**Created At**: {mem['created_at']}",
        f"**Updated At**: {mem['updated_at']}",
        f"",
        f"**Summary**:\n{mem['summary']}",
        f"",
        f"**Body**:\n{mem['body']}"
    ]
    return "\n".join(lines)


@client.tree.command(name="ask", description="SORA上のローカルLLMに質問します")
@app_commands.describe(question="質問内容")
async def ask(interaction: discord.Interaction, question: str) -> None:
    print(f"/ask from user_id={interaction.user.id}: {question}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        print("Calling Ollama...", flush=True)
        answer = await ask_ollama(
            base_url=OLLAMA_BASE_URL,
            model=DEFAULT_MODEL,
            prompt=question,
        )
    except Exception as exc:
        await interaction.followup.send(
            f"Ollama呼び出しでエラーが出ました: `{type(exc).__name__}: {exc}`"
        )
        return

    print("Got answer from Ollama.", flush=True)
    for chunk in split_message(answer):
        await interaction.followup.send(chunk)


@client.tree.command(name="remember", description="指定された内容を記憶します")
@app_commands.describe(
    title="記憶のタイトル", 
    body="記憶する本文", 
    tags="カンマ区切りのタグ (任意)", 
    memory_type="記憶の種別 (任意)", 
    sensitivity="秘匿性 (任意)"
)
async def remember(
    interaction: discord.Interaction, 
    title: str, 
    body: str, 
    tags: str = "", 
    memory_type: str = "conversation_note", 
    sensitivity: str = "normal"
) -> None:
    print(f"/remember from user_id={interaction.user.id}: title={title}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        mem_id = remember_memory(
            title=title, 
            body=body, 
            tags=tags, 
            memory_type=memory_type, 
            sensitivity=sensitivity
        )
        msg = (
            f"✅ 記憶しました。\n"
            f"**ID**: `{mem_id}`\n"
            f"**Title**: {title}\n"
            f"**Tags**: {tags}\n"
            f"**Sensitivity**: {sensitivity}"
        )
        await interaction.followup.send(msg)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="search", description="記憶を検索します")
@app_commands.describe(query="検索キーワード")
async def search(interaction: discord.Interaction, query: str) -> None:
    print(f"/search from user_id={interaction.user.id}: query={query}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        results = search_memories(query)
        if not results:
            await interaction.followup.send("見つかりませんでした。")
            return

        lines = [f"🔍 **検索結果** (上位{len(results)}件):"]
        for r in results:
            lines.append(f"- **{r['title']}** (`{r['id']}`) [{r['created_at']}]\n  Tags: {r['tags']}\n  {r['summary']}...")
        
        msg = "\n".join(lines)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)

    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="forget", description="記憶を無効化します")
@app_commands.describe(memory_id="無効化する記憶のID")
async def forget(interaction: discord.Interaction, memory_id: str) -> None:
    print(f"/forget from user_id={interaction.user.id}: memory_id={memory_id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        success = forget_memory(memory_id)
        if success:
            await interaction.followup.send(f"✅ 記憶 (`{memory_id}`) を無効化しました。")
        else:
            await interaction.followup.send(f"⚠️ 指定された記憶 (`{memory_id}`) は見つかりませんでした。")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="chat", description="自然文で指示を出します（記憶・検索・対話など）")
@app_commands.describe(text="自然文での指示や質問")
async def chat(interaction: discord.Interaction, text: str) -> None:
    print(f"/chat from user_id={interaction.user.id}: {text}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    is_recent = any(k in text for k in ["最近の記憶", "最近覚えたこと", "最新の記憶"]) or (
        "記憶" in text and "件" in text and any(k in text for k in ["見せて", "教えて", "表示"])
    )

    mem_id = extract_memory_id(text)
    is_show = (mem_id is not None) or (
        not is_recent and (
            "memory_id" in text or
            "の中身" in text or
            (any(k in text for k in ["記憶", "詳細"]) and any(k in text for k in ["見せて", "教えて", "表示"]))
        )
    )

    is_export = any(k in text for k in [
        "Markdownにして", "Markdownにエクスポート", "Markdown export", "Markdownに書き出",
        "記憶を書き出して", "記憶をエクスポート", "件エクスポート"
    ])

    is_remember = any(k in text for k in ["覚えて", "記憶して", "メモして", "保存して"])
    is_search = any(k in text for k in ["探して", "検索して", "前に", "覚えてる"])
    is_forget = any(k in text for k in ["消して", "忘れて", "削除して", "無効化して"])
    is_daily = any(k in text for k in ["まとめて", "日報", "今日の作業"])

    try:
        if is_export:
            limit = extract_limit(text, default=20, max_value=100)
            filepath, count = export_memories_to_markdown(limit=limit, memory_dir=MEMORY_DIR)
            if count == 0:
                await interaction.followup.send("エクスポート対象となる記憶がありませんでした。")
                return
            await interaction.followup.send(
                f"✅ 最近の記憶（{count}件）をMarkdownに書き出しました。\n"
                f"**出力先**: `{filepath}`"
            )
            return

        elif is_show:
            if mem_id:
                mem = get_memory(mem_id)
                if not mem:
                    await interaction.followup.send(f"⚠️ 指定された記憶 ID `{mem_id}` は見つかりませんでした。")
                    return
                intro = "指定された記憶を確認しました。詳細を表示します：\n\n"
                msg = intro + format_memory_detail(mem)
                for chunk in split_message(msg):
                    await interaction.followup.send(chunk)
            else:
                await interaction.followup.send(
                    "⚠️ 記憶の詳細を表示するには、`mem_` で始まる記憶IDを文中に含めるか、`/show_memory memory_id:...` コマンドを使用してください。\n"
                    "例：「記憶 mem_20260519_abcdef12 の詳細を見せて」"
                )
            return

        elif is_recent:
            limit = extract_limit(text, default=10, max_value=20)
            results = get_recent_memories(limit=limit)
            if not results:
                await interaction.followup.send("最近の記憶はありません。")
                return

            intro = "最近の記憶を表示します：\n\n"
            msg = intro + format_recent_memories(results)
            for chunk in split_message(msg):
                await interaction.followup.send(chunk)
            return

        elif is_daily:
            prompt = f"以下の作業メモを元に、日報形式（今日やったこと、決めたこと、次にやること、注意点など）に整理してください。\n\n作業メモ:\n{text}"
            print("Calling Ollama for daily report...", flush=True)
            answer = await ask_ollama(
                base_url=OLLAMA_BASE_URL,
                model=DEFAULT_MODEL,
                prompt=prompt,
            )
            title = "日報: " + text[:20].replace("\n", " ") + ("..." if len(text) > 20 else "")
            mem_id = remember_memory(
                title=title, 
                body=answer, 
                tags="daily_report", 
                memory_type="daily_report", 
                sensitivity="normal"
            )
            
            out_msg = f"✅ 日報を作成し、記憶しました (ID: `{mem_id}`).\n\n{answer}"
            
            combined = text + "\n" + answer
            candidate_msg = ""
            if detect_memory_candidate(combined):
                title_suggestion = "決定事項: " + text[:20].replace('\n', ' ') + ("..." if len(text) > 20 else "")
                body_suggestion = text.replace('\n', ' ').replace('`', '').replace('"', '\\"')
                if len(body_suggestion) > 100:
                    body_suggestion = body_suggestion[:100] + "..."
                
                candidate_msg = (
                    "\n\n💡 **個別記憶（決定事項など）の候補**\n"
                    "この日報には重要な決定や方針が含まれている可能性があります。\n"
                    "日報全体とは別に個別でプロジェクト記憶として保存したい場合は、以下を実行してください：\n"
                    f"```\n/remember title:{title_suggestion} body:{body_suggestion} tags:decision,project_note memory_type:project_note\n```"
                )
                
            chunks = split_message(out_msg)
            if candidate_msg:
                if len(chunks[-1]) + len(candidate_msg) <= 1900:
                    chunks[-1] += candidate_msg
                else:
                    chunks.append(candidate_msg)
                    
            for chunk in chunks:
                await interaction.followup.send(chunk)

        elif is_remember:
            title = text[:30].replace("\n", " ") + ("..." if len(text) > 30 else "")
            mem_id = remember_memory(
                title=title, 
                body=text, 
                tags="", 
                memory_type="conversation_note", 
                sensitivity="normal"
            )
            msg = f"✅ 以下の内容を記憶しました。\n**ID**: `{mem_id}`\n**Title**: {title}"
            await interaction.followup.send(msg)

        elif is_search:
            results = search_memories(text)
            if not results:
                await interaction.followup.send("関連する記憶は見つかりませんでした。")
                return

            lines = [f"🔍 **検索結果** (上位{len(results)}件):"]
            for r in results:
                lines.append(f"- **{r['title']}** (`{r['id']}`) [{r['created_at']}]\n  {r['summary']}...")
            
            msg = "\n".join(lines)
            for chunk in split_message(msg):
                await interaction.followup.send(chunk)

        elif is_forget:
            results = search_memories(text)
            if not results:
                await interaction.followup.send("削除・無効化の候補となる記憶は見つかりませんでした。")
                return

            lines = ["⚠️ 直接の削除や無効化は行いません。無効化するには以下のIDを指定して `/forget memory_id:...` を実行してください。\n", "🔍 **候補** (上位5件):"]
            for r in results:
                lines.append(f"- **{r['title']}** (`{r['id']}`)")
            
            msg = "\n".join(lines)
            for chunk in split_message(msg):
                await interaction.followup.send(chunk)

        else: # normal_chat
            print("Calling Ollama (chat)...", flush=True)
            answer = await ask_ollama(
                base_url=OLLAMA_BASE_URL,
                model=DEFAULT_MODEL,
                prompt=text,
            )
            print("Got answer from Ollama.", flush=True)
            
            combined = text + "\n" + answer
            candidate_msg = ""
            if detect_memory_candidate(combined):
                title_suggestion = text[:20].replace('\n', ' ') + ("..." if len(text) > 20 else "")
                body_suggestion = text.replace('\n', ' ').replace('`', '').replace('"', '\\"')
                if len(body_suggestion) > 100:
                    body_suggestion = body_suggestion[:100] + "..."
                
                candidate_msg = (
                    "\n\n💡 **長期記憶の候補を検出しました**\n"
                    "この会話には方針や決定などの重要な情報が含まれている可能性があります。\n"
                    "記憶に保存したい場合は、以下のコマンドをコピーして実行してください：\n"
                    f"```\n/remember title:{title_suggestion} body:{body_suggestion} tags:方針,決定\n```"
                )
            
            chunks = split_message(answer)
            if candidate_msg:
                if len(chunks[-1]) + len(candidate_msg) <= 1900:
                    chunks[-1] += candidate_msg
                else:
                    chunks.append(candidate_msg)
            
            for chunk in chunks:
                await interaction.followup.send(chunk)

    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="daily", description="作業メモを日報形式に整理して保存します")
@app_commands.describe(text="本日の作業内容やメモ")
async def daily_cmd(interaction: discord.Interaction, text: str) -> None:
    print(f"/daily from user_id={interaction.user.id}: {text[:50]}...", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        prompt = f"以下の作業メモを元に、日報形式（今日やったこと、決めたこと、次にやること、注意点など）に整理してください。\n\n作業メモ:\n{text}"
        print("Calling Ollama for /daily...", flush=True)
        answer = await ask_ollama(
            base_url=OLLAMA_BASE_URL,
            model=DEFAULT_MODEL,
            prompt=prompt,
        )
        title = "日報: " + text[:20].replace("\n", " ") + ("..." if len(text) > 20 else "")
        mem_id = remember_memory(
            title=title, 
            body=answer, 
            tags="daily_report", 
            memory_type="daily_report", 
            sensitivity="normal"
        )
        out_msg = f"✅ 日報を作成し、記憶しました (ID: `{mem_id}`).\n\n{answer}"
        
        combined = text + "\n" + answer
        candidate_msg = ""
        if detect_memory_candidate(combined):
            title_suggestion = "決定事項: " + text[:20].replace('\n', ' ') + ("..." if len(text) > 20 else "")
            body_suggestion = text.replace('\n', ' ').replace('`', '').replace('"', '\\"')
            if len(body_suggestion) > 100:
                body_suggestion = body_suggestion[:100] + "..."
            
            candidate_msg = (
                "\n\n💡 **個別記憶（決定事項など）の候補**\n"
                "この日報には重要な決定や方針が含まれている可能性があります。\n"
                "日報全体とは別に個別でプロジェクト記憶として保存したい場合は、以下を実行してください：\n"
                f"```\n/remember title:{title_suggestion} body:{body_suggestion} tags:decision,project_note memory_type:project_note\n```"
            )

        chunks = split_message(out_msg)
        if candidate_msg:
            if len(chunks[-1]) + len(candidate_msg) <= 1900:
                chunks[-1] += candidate_msg
            else:
                chunks.append(candidate_msg)
                
        for chunk in chunks:
            await interaction.followup.send(chunk)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="recent_memories", description="最近の記憶を表示します")
@app_commands.describe(limit="表示件数（デフォルト10）")
async def recent_memories_cmd(interaction: discord.Interaction, limit: int = 10) -> None:
    print(f"/recent_memories from user_id={interaction.user.id}: limit={limit}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    # 制限
    if limit > 20:
        limit = 20
    elif limit < 1:
        limit = 10

    await interaction.response.defer(thinking=True)
    try:
        results = get_recent_memories(limit=limit)
        if not results:
            await interaction.followup.send("最近の記憶はありません。")
            return

        msg = format_recent_memories(results)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)

    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="show_memory", description="指定した記憶の詳細を表示します")
@app_commands.describe(memory_id="表示する記憶のID")
async def show_memory_cmd(interaction: discord.Interaction, memory_id: str) -> None:
    print(f"/show_memory from user_id={interaction.user.id}: memory_id={memory_id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        mem = get_memory(memory_id)
        if not mem:
            await interaction.followup.send("見つかりませんでした。")
            return

        msg = format_memory_detail(mem)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)

    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="export_memory", description="記憶をMarkdownにエクスポートします")
@app_commands.describe(limit="出力件数（デフォルト20、最大100）")
async def export_memory_cmd(interaction: discord.Interaction, limit: int = 20) -> None:
    print(f"/export_memory from user_id={interaction.user.id}: limit={limit}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    # 制限
    if limit > 100:
        limit = 100
    elif limit < 1:
        limit = 20

    await interaction.response.defer(thinking=True)
    try:
        filepath, count = export_memories_to_markdown(limit=limit, memory_dir=MEMORY_DIR)
        
        if count == 0:
            await interaction.followup.send("エクスポートする記憶がありません。")
            return
            
        await interaction.followup.send(f"✅ {count}件の記憶をMarkdownにエクスポートしました。\n**出力先**: `{filepath}`")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


client.run(DISCORD_BOT_TOKEN)
