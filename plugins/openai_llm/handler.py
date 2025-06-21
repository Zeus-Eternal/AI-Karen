try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    openai = None

async def run(params: dict) -> str:
    prompt = params.get("prompt", "")
    max_tokens = int(params.get("max_tokens", 128))
    model = params.get("model", "gpt-3.5-turbo")
    if openai is None:
        return f"{prompt} (openai unavailable)"
    resp = await openai.ChatCompletion.acreate(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
