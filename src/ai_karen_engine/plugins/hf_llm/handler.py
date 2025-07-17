from ai_karen_engine.integrations.llm_utils import LLMUtils

llm = LLMUtils()

async def run(params: dict) -> str:
    prompt = params.get("prompt", "")
    max_tokens = int(params.get("max_tokens", 128))
    return llm.generate_text(prompt, max_tokens=max_tokens)
