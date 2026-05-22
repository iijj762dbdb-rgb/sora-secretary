import discord
from discord import app_commands
from discord.ext import tasks
import re

from config import (
    DISCORD_BOT_TOKEN,
    ALLOWED_DISCORD_USER_IDS,
    OLLAMA_BASE_URL,
    DEFAULT_MODEL,
    SUMMARY_MODEL,
    DISCORD_GUILD_ID_INT,
    MEMORY_DIR,
    ENABLE_MESSAGE_CONTENT_INTENT,
    MESSAGE_CONTENT_PREFIX,
    MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS,
    ASSISTANT_NAME,
    ASSISTANT_PERSONA,
    validate_bot_config,
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
    lint_memories,
    create_todo,
    list_todos,
    get_todo,
    complete_todo,
    archive_todo,
    create_reminder,
    list_pending_reminders,
    list_due_reminders,
    mark_reminder_sent,
    cancel_reminder,
)
from status_info import build_status_report


class SoraSecretary(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        if hasattr(intents, "guild_messages"):
            intents.guild_messages = True
        if hasattr(intents, "dm_messages"):
            intents.dm_messages = True
        if ENABLE_MESSAGE_CONTENT_INTENT:
            intents.message_content = True
        print(f"message_content_debug: ENABLE_MESSAGE_CONTENT_INTENT={ENABLE_MESSAGE_CONTENT_INTENT}", flush=True)
        print(f"message_content_debug: intents.guilds={intents.guilds}", flush=True)
        print(f"message_content_debug: intents.messages={intents.messages}", flush=True)
        print(f"message_content_debug: intents.guild_messages={getattr(intents, 'guild_messages', None)}", flush=True)
        print(f"message_content_debug: intents.dm_messages={getattr(intents, 'dm_messages', None)}", flush=True)
        print(f"message_content_debug: intents.message_content={intents.message_content}", flush=True)
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

        self.reminder_loop.start()

    @tasks.loop(seconds=60.0)
    async def reminder_loop(self) -> None:
        try:
            from datetime import datetime
            now_iso = datetime.now().isoformat()
            due_reminders = list_due_reminders(now_iso)
            for r in due_reminders:
                if not ALLOWED_DISCORD_USER_IDS:
                    break
                user_id = list(ALLOWED_DISCORD_USER_IDS)[0]
                user = self.get_user(user_id)
                if user is None:
                    try:
                        user = await self.fetch_user(user_id)
                    except:
                        pass

                if user:
                    msg = f"⏰ **Reminder**\n{r['text']}"
                    await user.send(msg)
                    mark_reminder_sent(r['id'])
                else:
                    print(f"Failed to find user {user_id} for reminder {r['id']}")
        except Exception as e:
            print(f"Error in reminder loop: {e}")

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.wait_until_ready()

    async def on_ready(self) -> None:
        init_db()
        print("assistant_memory database initialized.", flush=True)
        print(f"Logged in as {self.user}.")

    async def on_message(self, message: discord.Message) -> None:
        print(f"message_content_debug: on_message called user_id={message.author.id} bot={message.author.bot} channel_id={message.channel.id}", flush=True)
        if not ENABLE_MESSAGE_CONTENT_INTENT:
            print("message_content_debug: ignored because ENABLE_MESSAGE_CONTENT_INTENT is False", flush=True)
            return
        if message.author == self.user:
            return
        if message.author.bot:
            print("message_content_debug: ignored because author is a bot", flush=True)
            return
        if not is_allowed(message.author.id):
            print(f"message_content_debug: ignored because user_id={message.author.id} is not allowed", flush=True)
            return
        if MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS and message.channel.id not in MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS:
            print(f"message_content_debug: ignored because channel_id={message.channel.id} is not in allowed list", flush=True)
            return

        content = message.content.strip()
        has_prefix = False
        has_mention = False
        trigger_len = 0

        # Log content snippet safely (up to 30 chars)
        safe_snippet = content[:30].replace("\n", " ") + ("..." if len(content) > 30 else "")
        print(f"message_content_debug: content_snippet={safe_snippet!r} MESSAGE_CONTENT_PREFIX={MESSAGE_CONTENT_PREFIX!r}", flush=True)

        if content.startswith(MESSAGE_CONTENT_PREFIX):
            has_prefix = True
            trigger_len = len(MESSAGE_CONTENT_PREFIX)
        else:
            mentions_to_check = [f"<@!{self.user.id}>", f"<@{self.user.id}>"]
            for mention in mentions_to_check:
                if content.startswith(mention):
                    has_mention = True
                    trigger_len = len(mention)
                    break

        print(f"message_content_debug: has_prefix={has_prefix} has_mention={has_mention}", flush=True)

        if not has_prefix and not has_mention:
            print("message_content_debug: ignored because no prefix or mention matched", flush=True)
            return

        text = content[trigger_len:].strip()
        if not text:
            print("message_content_debug: ignored because cleaned text is empty", flush=True)
            return

        if len(text) > 4000:
            await message.channel.send("⚠️ 送信されたテキストが長すぎます（最大4000文字）。")
            return

        safe_cleaned = text[:30].replace("\n", " ") + ("..." if len(text) > 30 else "")
        print(f"message_content_debug: run_chat_flow reached, cleaned_text={safe_cleaned!r}", flush=True)

        async with message.channel.typing():
            try:
                chunks = await run_chat_flow(text)
                for chunk in chunks:
                    await message.channel.send(chunk)
            except Exception as exc:
                await message.channel.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


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


async def run_chat_flow(text: str) -> list[str]:
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

    is_todo_add = any(k in text for k in ["ToDoに入れて", "をやることに追加", "todoに追加"])
    is_todo_list = any(k in text for k in ["タスク一覧", "今日やること", "todo一覧"])

    is_remind = any(k in text for k in ["リマインドして", "あとで通知して", "remind me"])
    is_briefing = any(k in text for k in ["ブリーフィング", "朝のサマリー", "夜のサマリー", "今日の状況"])

    match_todo = re.search(r'todo_[a-zA-Z0-9_]+', text)
    todo_id_in_text = match_todo.group(0) if match_todo else None
    is_todo_done = any(k in text for k in ["完了", "終わった", "終えた"]) and todo_id_in_text is not None

    if is_export:
        limit = extract_limit(text, default=20, max_value=100)
        filepath, count = export_memories_to_markdown(limit=limit, memory_dir=MEMORY_DIR)
        if count == 0:
            return ["エクスポート対象となる記憶がありませんでした。"]
        return [
            f"✅ 最近の記憶（{count}件）をMarkdownに書き出しました。\n"
            f"**出力先**: `{filepath}`"
        ]

    elif is_briefing:
        briefing_text = await execute_briefing()
        return split_message(briefing_text)

    elif is_remind:
        match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?[+-]\d{2}:\d{2}', text)
        if match:
            original_time_str = match.group(0)
            remind_at = original_time_str

            if remind_at.count(':') == 2:
                tz_idx = remind_at.find('+', 10)
                if tz_idx == -1:
                    tz_idx = remind_at.find('-', 10)
                if tz_idx != -1:
                    remind_at = remind_at[:tz_idx] + ':00' + remind_at[tz_idx:]

            remind_text = text.replace(original_time_str, "").replace("リマインドして", "").replace("あとで通知して", "").replace("remind me", "").strip()
            if not remind_text:
                remind_text = "リマインダー"
            rem_id = create_reminder(text=remind_text, remind_at=remind_at)
            return [f"✅ 以下のリマインダーを追加しました。\n**ID**: `{rem_id}`\n**Time**: `{remind_at}`\n**Text**: {remind_text}"]
        else:
            return ["⚠️ リマインダーを追加するには、日時の指定が必要です (例: `2026-05-20T21:00:00+09:00`)。\nコマンド `/remind_add` を使用することもできます。"]

    elif is_todo_done:
        success = complete_todo(todo_id_in_text)
        if success:
            return [f"✅ タスク `{todo_id_in_text}` を完了にしました。お疲れ様でした！"]
        else:
            return [f"⚠️ 指定されたタスク `{todo_id_in_text}` は見つかりませんでした。"]

    elif any(k in text for k in ["終わった", "完了"]) and not is_show and not is_search:
        return ["💡 タスクを完了にする場合は、「todo_xxx を完了」のようにIDを含めて指示してください。\n（タスク一覧を確認するには「タスク一覧」と言ってください）"]

    elif is_todo_list:
        todos = list_todos(status="todo", limit=10)
        doing = list_todos(status="doing", limit=5)
        lines = ["📝 **現在のタスク**"]
        if doing:
            lines.append("\n▶️ **Doing (対応中)**:")
            for t in doing:
                lines.append(f"- **{t['title']}** (`{t['id']}`)")
        if todos:
            lines.append("\n✅ **ToDo (未完了)**:")
            for t in todos:
                lines.append(f"- **{t['title']}** (`{t['id']}`)")
        if not todos and not doing:
            lines.append("\n現在、対応中のタスクや未完了のタスクはありません。")
        return split_message("\n".join(lines))

    elif is_todo_add:
        title = text.replace("これToDoに入れて", "").replace("をやることに追加", "").replace("todoに追加", "").strip()
        if not title:
            title = "新しいタスク"
        title = title[:50]
        todo_id = create_todo(title=title, body=text)
        return [f"✅ 以下のタスクをToDoに追加しました。\n**ID**: `{todo_id}`\n**Title**: {title}"]

    elif is_show:
        if mem_id:
            mem = get_memory(mem_id)
            if not mem:
                return [f"⚠️ 指定された記憶 ID `{mem_id}` は見つかりませんでした。"]
            intro = "指定された記憶を確認しました。詳細を表示します：\n\n"
            msg = intro + format_memory_detail(mem)
            return split_message(msg)
        else:
            return [
                "⚠️ 記憶の詳細を表示するには、`mem_` で始まる記憶IDを文中に含めるか、`/show_memory memory_id:...` コマンドを使用してください。\n"
                "例：「記憶 mem_20260519_abcdef12 の詳細を見せて」"
            ]

    elif is_recent:
        limit = extract_limit(text, default=10, max_value=20)
        results = get_recent_memories(limit=limit)
        if not results:
            return ["最近の記憶はありません。"]

        intro = "最近の記憶を表示します：\n\n"
        msg = intro + format_recent_memories(results)
        return split_message(msg)

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
        return chunks

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
        return [msg]

    elif is_search:
        results = search_memories(text)
        if not results:
            return ["関連する記憶は見つかりませんでした。"]

        lines = [f"🔍 **検索結果** (上位{len(results)}件):"]
        for r in results:
            lines.append(f"- **{r['title']}** (`{r['id']}`) [{r['created_at']}]\n  {r['summary']}...")

        msg = "\n".join(lines)
        return split_message(msg)

    elif is_forget:
        results = search_memories(text)
        if not results:
            return ["削除・無効化の候補となる記憶は見つかりませんでした。"]

        lines = ["⚠️ 直接の削除や無効化は行いません。無効化するには以下のIDを指定して `/forget memory_id:...` を実行してください。\n", "🔍 **候補** (上位5件):"]
        for r in results:
            lines.append(f"- **{r['title']}** (`{r['id']}`)")

        msg = "\n".join(lines)
        return split_message(msg)

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
    try:
        chunks = await run_chat_flow(text)
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
            model=SUMMARY_MODEL,
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


@client.tree.command(name="status", description="システムおよびBotの稼働ステータスを表示します")
async def status_cmd(interaction: discord.Interaction) -> None:
    print(f"/status from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        report = await build_status_report()
        chunks = split_message(report)
        for chunk in chunks:
            await interaction.followup.send(chunk)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="todo_add", description="新しいToDoを追加します")
@app_commands.describe(title="タスクのタイトル", body="詳細", due="期限(任意)", priority="優先度(low/normal/high)")
async def todo_add_cmd(interaction: discord.Interaction, title: str, body: str = "", due: str = None, priority: str = "normal") -> None:
    print(f"/todo_add from user_id={interaction.user.id}: title={title}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        todo_id = create_todo(title=title, body=body, priority=priority, due_at=due)
        await interaction.followup.send(f"✅ ToDoを追加しました。\n**ID**: `{todo_id}`\n**Title**: {title}\n**Priority**: {priority}")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")

@client.tree.command(name="todo_list", description="ToDo一覧を表示します")
@app_commands.describe(status="絞り込むステータス(todo/doing/done)")
async def todo_list_cmd(interaction: discord.Interaction, status: str = None) -> None:
    print(f"/todo_list from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        todos = list_todos(status=status, limit=20)
        if not todos:
            await interaction.followup.send("タスクはありません。")
            return

        lines = [f"📝 **ToDo一覧** {f'({status})' if status else ''}"]
        for t in todos:
            lines.append(f"- **{t['title']}** (`{t['id']}`) [{t['status']}]")

        msg = "\n".join(lines)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")

@client.tree.command(name="todo_done", description="指定したToDoを完了にします")
@app_commands.describe(todo_id="完了にするToDoのID")
async def todo_done_cmd(interaction: discord.Interaction, todo_id: str) -> None:
    print(f"/todo_done from user_id={interaction.user.id}: {todo_id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        success = complete_todo(todo_id)
        if success:
            await interaction.followup.send(f"✅ タスク `{todo_id}` を完了にしました。お疲れ様でした！")
        else:
            await interaction.followup.send(f"⚠️ タスク `{todo_id}` は見つかりませんでした。")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")

@client.tree.command(name="todo_show", description="指定したToDoの詳細を表示します")
@app_commands.describe(todo_id="表示するToDoのID")
async def todo_show_cmd(interaction: discord.Interaction, todo_id: str) -> None:
    print(f"/todo_show from user_id={interaction.user.id}: {todo_id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        t = get_todo(todo_id)
        if not t:
            await interaction.followup.send(f"⚠️ タスク `{todo_id}` は見つかりませんでした。")
            return

        lines = [
            f"📄 **ToDo詳細** (`{t['id']}`)",
            f"**Title**: {t['title']}",
            f"**Status**: {t['status']}",
            f"**Priority**: {t['priority']}",
            f"**Due At**: {t['due_at']}",
            f"**Created At**: {t['created_at']}",
            f"**Completed At**: {t['completed_at']}",
            f"",
            f"**Body**:\n{t['body']}"
        ]
        msg = "\n".join(lines)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="briefing", description="現在のタスク・記憶・リマインダーを元に今日の状況を整理します")
async def briefing_cmd(interaction: discord.Interaction) -> None:
    print(f"/briefing from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        print("Calling Ollama for /briefing...", flush=True)
        answer = await execute_briefing()
        for chunk in split_message(answer):
            await interaction.followup.send(chunk)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


@client.tree.command(name="remind_add", description="新しいリマインダーを追加します")
@app_commands.describe(text="通知する内容", remind_at="日時 (ISO8601形式: 例 2026-05-20T21:00:00+09:00)")
async def remind_add_cmd(interaction: discord.Interaction, text: str, remind_at: str) -> None:
    print(f"/remind_add from user_id={interaction.user.id}: {text}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        rem_id = create_reminder(text=text, remind_at=remind_at)
        await interaction.followup.send(f"✅ リマインダーを追加しました。\n**ID**: `{rem_id}`\n**Time**: `{remind_at}`\n**Text**: {text}")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")

@client.tree.command(name="remind_list", description="待機中のリマインダー一覧を表示します")
async def remind_list_cmd(interaction: discord.Interaction) -> None:
    print(f"/remind_list from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        reminders = list_pending_reminders(limit=20)
        if not reminders:
            await interaction.followup.send("待機中のリマインダーはありません。")
            return

        lines = ["⏰ **Pending Reminders**"]
        for r in reminders:
            lines.append(f"• [`{r['id']}`] {r['text']}\n  at: {r['remind_at']}")

        msg = "\n".join(lines)
        for chunk in split_message(msg):
            await interaction.followup.send(chunk)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")

@client.tree.command(name="remind_done", description="リマインダーを完了(sent)状態にします")
@app_commands.describe(remind_id="対象のID")
async def remind_done_cmd(interaction: discord.Interaction, remind_id: str) -> None:
    print(f"/remind_done from user_id={interaction.user.id}: {remind_id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        success = mark_reminder_sent(remind_id)
        if success:
            await interaction.followup.send(f"✅ リマインダー `{remind_id}` を sent 状態にしました。")
        else:
            await interaction.followup.send(f"⚠️ リマインダー `{remind_id}` は見つかりませんでした。")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")

@client.tree.command(name="remind_cancel", description="リマインダーをキャンセル状態にします")
@app_commands.describe(remind_id="対象のID")
async def remind_cancel_cmd(interaction: discord.Interaction, remind_id: str) -> None:
    print(f"/remind_cancel from user_id={interaction.user.id}: {remind_id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    try:
        success = cancel_reminder(remind_id)
        if success:
            await interaction.followup.send(f"✅ リマインダー `{remind_id}` をキャンセルしました。")
        else:
            await interaction.followup.send(f"⚠️ リマインダー `{remind_id}` は見つかりませんでした。")
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`")


def format_memory_lint(res: dict) -> str:
    summary = (
        f"📊 **記憶データベース点検レポート (Memory Lint)**\n\n"
        f"**1. 件数サマリー**\n"
        f"- 総記憶数: `{res['total_count']}` 件\n"
        f"- 有効記憶数 (archived=0): `{res['active_count']}` 件\n"
        f"- 無効記憶数 (archived=1): `{res['archived_count']}` 件\n"
    )

    type_strs = []
    for mtype, count in res["type_breakdown"].items():
        type_strs.append(f"  - `{mtype}`: {count} 件")
    type_info = "**2. タイプ別内訳**\n" + ("\n".join(type_strs) if type_strs else "  - なし")

    warnings = []

    if res["empty_tags"]:
        tag_items = ", ".join([f"`{r['id']}`({r['title'][:10]}...)" for r in res["empty_tags"]])
        warnings.append(f"⚠️ **タグ未設定 (空タグ) の記憶** ({len(res['empty_tags'])}件検出):\n  - 該当例: {tag_items}")

    if res["short_title"]:

        title_items = ", ".join([f"`{r['id']}`({r['title']})" for r in res["short_title"]])
        warnings.append(f"⚠️ **タイトルが短すぎる記憶 (5文字未満)** ({len(res['short_title'])}件検出):\n  - 該当例: {title_items}")

    if res["short_body"]:
        body_items = ", ".join([f"`{r['id']}`({r['title'][:10]}...)" for r in res["short_body"]])
        warnings.append(f"⚠️ **本文が極端に短いか未入力の記憶 (10文字未満)** ({len(res['short_body'])}件検出):\n  - 該当例: {body_items}")

    if res["long_body"]:
        long_items = ", ".join([f"`{r['id']}`({r['title'][:10]}...)" for r in res["long_body"]])
        warnings.append(f"⚠️ **本文が長すぎる記憶 (2000文字超)** ({len(res['long_body'])}件検出):\n  - 該当例: {long_items}")

    if res["sensitivity_normal_count"] > 0:
        warnings.append(f"ℹ️ **秘匿性がデフォルト (normal) のままの記憶**: `{res['sensitivity_normal_count']}` 件\n  - 必要に応じて適切な公開/秘匿レベルの見直しを推奨します。")

    daily_count = res["type_breakdown"].get("daily_report", 0)
    if daily_count > 30:
        warnings.append(f"💡 **日報 (daily_report) が多すぎる注意** ({daily_count}件検出):\n  - 登録件数が30件を超えています。古い日報の整理、あるいはアーカイブ化を検討してください。")

    if res["duplicates"]:
        dup_items = ", ".join([f"\"{r['title']}\"({r['c']}回)" for r in res["duplicates"]])
        warnings.append(f"⚠️ **重複タイトルの候補**: {dup_items}\n  - 同じタイトルの記憶が複数存在します。名寄せや集約を推奨します。")

    warnings_info = "**3. 要確認・改善候補**\n" + ("\n\n".join(warnings) if warnings else "✅ 特に要確認の記憶候補はありません。健全なデータベース状態です。")

    old_strs = []
    for r in res["old_memories"]:
        old_strs.append(f"  - `{r['created_at']}` | `{r['id']}` | `{r['memory_type']}` | **{r['title']}**")
    old_info = "**4. 長期保存中の記憶候補 (古い決定事項・プロジェクトノート)**\n" + ("\n".join(old_strs) if old_strs else "  - 該当する古い記憶はありません")
    old_info += "\n\n※ これらは自動アーカイブされません。詳細確認には `/show_memory <ID>`、不要な場合は `/forget <ID>` をご活用ください。"

    report = (
        f"{summary}\n"
        f"{type_info}\n\n"
        f"{warnings_info}\n\n"
        f"{old_info}"
    )
    return report


@client.tree.command(name="memory_lint", description="記憶DBを点検し、タグ無しや重複などの改善候補リストを表示します")
async def memory_lint_cmd(interaction: discord.Interaction) -> None:
    print(f"/memory_lint from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        res = lint_memories()
        report = format_memory_lint(res)
        chunks = split_message(report)
        for chunk in chunks:
            await interaction.followup.send(chunk, ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`", ephemeral=True)



# Message Context Menu: 記憶する

@client.tree.context_menu(name="記憶する")
async def context_remember(interaction: discord.Interaction, message: discord.Message) -> None:
    print(f"Context menu [記憶する] from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        content = message.content
        if not content.strip():
            await interaction.followup.send("⚠️ メッセージ本文が空のため、記憶できません。", ephemeral=True)
            return

        if is_sensitive(content):
            await interaction.followup.send(
                "⚠️ 個人情報や機密性の高い単語（パスワード、トークン、秘密鍵など）が含まれている可能性があるため、記憶できません。",
                ephemeral=True
            )
            return

        title = content[:30].replace("\n", " ") + ("..." if len(content) > 30 else "")
        mem_id = remember_memory(
            title=title,
            body=content,
            tags="",
            memory_type="conversation_note",
            sensitivity="normal"
        )
        msg = (
            f"✅ 選択したメッセージを記憶しました。\n"
            f"**ID**: `{mem_id}`\n"
            f"**Title**: {title}"
        )
        await interaction.followup.send(msg, ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`", ephemeral=True)


# Message Context Menu: 日報にする
@client.tree.context_menu(name="日報にする")
async def context_daily(interaction: discord.Interaction, message: discord.Message) -> None:
    print(f"Context menu [日報にする] from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        content = message.content
        if not content.strip():
            await interaction.followup.send("⚠️ メッセージ本文が空のため、日報化できません。", ephemeral=True)
            return

        prompt = f"以下の作業メモを元に、日報形式（今日やったこと、決めたこと、次にやること、注意点など）に整理してください。\n\n作業メモ:\n{content}"
        print("Calling Ollama for context menu daily report...", flush=True)
        answer = await ask_ollama(
            base_url=OLLAMA_BASE_URL,
            model=DEFAULT_MODEL,
            prompt=prompt,
        )
        title = "日報: " + content[:20].replace("\n", " ") + ("..." if len(content) > 20 else "")
        mem_id = remember_memory(
            title=title,
            body=answer,
            tags="daily_report",
            memory_type="daily_report",
            sensitivity="normal"
        )
        out_msg = f"✅ 日報を作成し、記憶しました (ID: `{mem_id}`).\n\n{answer}"

        combined = content + "\n" + answer
        candidate_msg = ""
        if detect_memory_candidate(combined):
            title_suggestion = "決定事項: " + content[:20].replace('\n', ' ') + ("..." if len(content) > 20 else "")
            body_suggestion = content.replace('\n', ' ').replace('`', '').replace('"', '\\"')
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
            await interaction.followup.send(chunk, ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`", ephemeral=True)


# Message Context Menu: 要約する
@client.tree.context_menu(name="要約する")
async def context_summarize(interaction: discord.Interaction, message: discord.Message) -> None:
    print(f"Context menu [要約する] from user_id={interaction.user.id}", flush=True)
    if not is_allowed(interaction.user.id):
        await interaction.response.send_message("このBotを使う権限がありません。", ephemeral=True)
        return

    await interaction.response.defer(thinking=True, ephemeral=True)
    try:
        content = message.content
        if not content.strip():
            await interaction.followup.send("⚠️ メッセージ本文が空のため、要約できません。", ephemeral=True)
            return

        prompt = f"以下の文章を短く要約してください。\n\n文章:\n{content}"
        print("Calling Ollama for context menu summarize...", flush=True)
        answer = await ask_ollama(
            base_url=OLLAMA_BASE_URL,
            model=DEFAULT_MODEL,
            prompt=prompt,
        )
        msg = f"📝 **要約結果**:\n\n{answer}"
        for chunk in split_message(msg):
            await interaction.followup.send(chunk, ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"エラーが発生しました: `{type(exc).__name__}: {exc}`", ephemeral=True)


async def execute_briefing() -> str:
    todos_doing = list_todos(status="doing", limit=5)
    todos_todo = list_todos(status="todo", limit=5)
    reminders = list_pending_reminders(limit=5)
    memories = get_recent_memories(limit=3)

    state_lines = []
    state_lines.append("[現在のリマインダー (Pending)]")
    for r in reminders:
        state_lines.append(f"- {r['text']} (期限: {r['remind_at']})")
    if not reminders:
        state_lines.append("- なし")

    state_lines.append("\n[進行中のタスク (Doing)]")
    for t in todos_doing:
        due = t.get('due_at') or '未定'
        state_lines.append(f"- {t['title']} (期限: {due})")
    if not todos_doing:
        state_lines.append("- なし")

    state_lines.append("\n[未着手のタスク (ToDo)]")
    for t in todos_todo:
        due = t.get('due_at') or '未定'
        state_lines.append(f"- {t['title']} (期限: {due})")
    if not todos_todo:
        state_lines.append("- なし")

    state_lines.append("\n[最近の記憶 (Memories)]")
    for m in memories:
        state_lines.append(f"- {m['title']}")
    if not memories:
        state_lines.append("- なし")

    state_text = "\n".join(state_lines)

    prompt = (
        f"あなたは「{ASSISTANT_NAME}」という名前の秘書AIです。以下の現在の状況（タスク、リマインダー、記憶）を元に、"
        "本日のブリーフィング（挨拶、今日の状況の要約、注意すべきタスクやリマインダーなど）を作成してください。\n"
        "簡潔で丁寧な口調でお願いします。\n\n"
        f"【現在の状況】\n{state_text}"
    )

    answer = await ask_ollama(
        base_url=OLLAMA_BASE_URL,
        model=SUMMARY_MODEL,
        prompt=prompt,
        system_prompt=ASSISTANT_PERSONA
    )

    return answer


if __name__ == '__main__':
    validate_bot_config()
    client.run(DISCORD_BOT_TOKEN)
