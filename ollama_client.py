import httpx

from config import (
    CHAT_MODEL,
    DEFAULT_MODEL,
    SUMMARY_MODEL,
    ASSISTANT_NAME,
    ASSISTANT_PERSONA,
)


def resolve_ollama_model(model: str, prompt: str) -> str:
    """Return the configured model for the current lightweight routing phase."""
    if "日報形式" in prompt or "短く要約" in prompt:
        return SUMMARY_MODEL
    if model == DEFAULT_MODEL:
        return CHAT_MODEL
    return model


async def ask_ollama(base_url: str, model: str, prompt: str) -> str:
    if ASSISTANT_PERSONA == "calm_secretary":
        system_prompt = (
            f"あなたの名前は「{ASSISTANT_NAME}」です。落ち着いた雰囲気の個人秘書として振る舞ってください。\n"
            "以下のルールを厳守してください：\n"
            "1. 日本語で丁寧かつ簡潔（短め）に、少し親しみやすさを持って返答してください。\n"
            "2. ユーザーの作業やタスクを整理するのが得意で、次にやるべきアクションを明確にする手助けをしてください。\n"
            "3. 不確かなことは不確かであると伝え、記憶データベース（DB）にないことを覚えていると嘘をつかないでください。\n"
            "4. ファイルやデータの削除、復元、DB変更、rsync --delete、fsck、大量のbackfillなどの危険操作は絶対に実行せず、提案や警告を提示するのみに留めてください。"
        )
    else:
        system_prompt = (
            f"あなたの名前は「{ASSISTANT_NAME}」です。日本語で、丁寧かつ短めに返答してください。\n"
            "危険操作、削除、復元、DB変更、rsync --delete、fsck、大量backfillは実行せず、提案だけに留めてください。"
        )

    selected_model = resolve_ollama_model(model=model, prompt=prompt)

    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(f"{base_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

    return data.get("message", {}).get("content", "").strip() or "返答が空でした。"
