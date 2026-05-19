import httpx

from config import CHAT_MODEL, DEFAULT_MODEL, SUMMARY_MODEL


def resolve_ollama_model(model: str, prompt: str) -> str:
    """Return the configured model for the current lightweight routing phase."""
    if "日報形式" in prompt or "短く要約" in prompt:
        return SUMMARY_MODEL
    if model == DEFAULT_MODEL:
        return CHAT_MODEL
    return model


async def ask_ollama(base_url: str, model: str, prompt: str) -> str:
    system_prompt = (
        "あなたはSORA上で動く個人用のローカル秘書AIです。"
        "返答は日本語で、丁寧かつ短めにしてください。"
        "危険操作、削除、復元、DB変更、rsync --delete、fsck、大量backfillは実行せず、"
        "提案だけに留めてください。"
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
