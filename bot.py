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


client.run(DISCORD_BOT_TOKEN)
