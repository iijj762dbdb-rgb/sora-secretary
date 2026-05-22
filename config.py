import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:4b")
CHAT_MODEL = os.getenv("CHAT_MODEL", DEFAULT_MODEL)
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", DEFAULT_MODEL)
CODE_MODEL = os.getenv("CODE_MODEL", DEFAULT_MODEL)
ASSISTANT_MEMORY_DB = os.getenv("ASSISTANT_MEMORY_DB", "./data/assistant_memory.db")
MEMORY_DIR = os.getenv("MEMORY_DIR", "./memory")

_raw_allowed_ids = os.getenv("ALLOWED_DISCORD_USER_IDS", "")
ALLOWED_DISCORD_USER_IDS = set()

for value in _raw_allowed_ids.split(","):
    value = value.strip()
    if not value:
        continue
    if not value.isdigit():
        raise RuntimeError(
            "ALLOWED_DISCORD_USER_IDS must be numeric Discord user IDs, "
            f"but got: {value!r}"
        )
    ALLOWED_DISCORD_USER_IDS.add(int(value))

DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")
DISCORD_GUILD_ID_INT = int(DISCORD_GUILD_ID) if DISCORD_GUILD_ID.strip().isdigit() else None

ENABLE_MESSAGE_CONTENT_INTENT = os.getenv("ENABLE_MESSAGE_CONTENT_INTENT", "false").lower() == "true"
MESSAGE_CONTENT_PREFIX = os.getenv("MESSAGE_CONTENT_PREFIX", "sora:")

_raw_channel_ids = os.getenv("MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS", "")
MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS = set()
for value in _raw_channel_ids.split(","):
    value = value.strip()
    if not value:
        continue
    if not value.isdigit():
        raise RuntimeError(
            "MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS must be numeric Discord channel IDs, "
            f"but got: {value!r}"
        )
    MESSAGE_CONTENT_ALLOWED_CHANNEL_IDS.add(int(value))

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "SORA Secretary")
ASSISTANT_PERSONA = os.getenv("ASSISTANT_PERSONA", "calm_secretary")


def validate_bot_config() -> None:
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set")

    if not ALLOWED_DISCORD_USER_IDS:
        raise RuntimeError("ALLOWED_DISCORD_USER_IDS is not set")
