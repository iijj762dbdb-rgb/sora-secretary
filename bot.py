import discord
from discord import app_commands

from config import (
    DISCORD_BOT_TOKEN,
    ALLOWED_DISCORD_USER_IDS,
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    DISCORD_GUILD_ID_INT,
)
from ollama_client import ask_ollama
from assistant_memory import init_db, remember_memory, search_memories, forget_memory, get_recent_memories


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

    is_recent = any(k in text for k in ["最近覚えたことを見せて", "最近の記憶"])
    is_remember = any(k in text for k in ["覚えて", "記憶して", "メモして", "保存して"])
    is_search = any(k in text for k in ["探して", "検索して", "前に", "覚えてる"])
    is_forget = any(k in text for k in ["消して", "忘れて", "削除して"])
    is_daily = any(k in text for k in ["まとめて", "日報", "今日の作業"])

    try:
        if is_recent:
            results = get_recent_memories(limit=10)
            if not results:
                await interaction.followup.send("最近の記憶はありません。")
                return

            lines = [f"🕒 **最近の記憶** (上位{len(results)}件):"]
            for r in results:
                lines.append(f"- **{r['title']}** (`{r['id']}`) [{r['created_at']}]\n  {r['summary']}...")
            
            msg = "\n".join(lines)
            for chunk in split_message(msg):
                await interaction.followup.send(chunk)

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
            for chunk in split_message(out_msg):
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
            for chunk in split_message(answer):
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
        for chunk in split_message(out_msg):
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

        lines = [f"🕒 **最近の記憶** (上位{len(results)}件):"]
        for r in results:
            lines.append(f"- **{r['title']}** (`{r['id']}`) [{r['created_at']}]\n  Tags: {r['tags']}\n  {r['summary']}...")
        
        msg = "\n".join(lines)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)

    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


client.run(DISCORD_BOT_TOKEN)
