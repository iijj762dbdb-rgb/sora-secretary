import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:4b")

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

if not DISCORD_BOT_TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN is not set")

if not ALLOWED_DISCORD_USER_IDS:
    raise RuntimeError("ALLOWED_DISCORD_USER_IDS is not set")

DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")
DISCORD_GUILD_ID_INT = int(DISCORD_GUILD_ID) if DISCORD_GUILD_ID.strip().isdigit() else None
