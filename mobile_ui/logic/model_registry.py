MODEL_REGISTRY = {
    "Local (Ollama)": [
        {"name": "llama3.2:latest", "size": "7B", "speed": "fast", "type": "chat"},
        {"name": "mistral", "size": "7B", "speed": "fast", "type": "chat"},
        {"name": "codellama", "size": "7B", "speed": "fast", "type": "code"},
    ],
    "OpenAI": [
        {"name": "gpt-4o", "size": "n/a", "speed": "fast", "type": "chat"},
        {"name": "gpt-3.5-turbo", "size": "n/a", "speed": "fast", "type": "chat"},
    ],
    "Anthropic": [
        {"name": "claude-3-opus", "size": "n/a", "speed": "fast", "type": "chat"},
        {"name": "claude-3-haiku", "size": "n/a", "speed": "fast", "type": "chat"},
    ],
    "Gemini": [
        {"name": "gemini-pro", "size": "n/a", "speed": "fast", "type": "chat"},
        {"name": "gemini-pro-vision", "size": "n/a", "speed": "fast", "type": "chat"},
    ],
    "Groq": [
        {"name": "llama3-70b", "size": "70B", "speed": "fast", "type": "chat"},
        {"name": "mixtral-8x7b", "size": "56B", "speed": "fast", "type": "chat"},
    ],
    "HuggingFace": [
        {"name": "gpt2", "size": "small", "speed": "fast", "type": "chat"},
        {"name": "bloom", "size": "176B", "speed": "slow", "type": "chat"},
        {"name": "falcon-7b", "size": "7B", "speed": "medium", "type": "chat"},
    ],
    "Cohere": [
        {"name": "command-r", "size": "n/a", "speed": "fast", "type": "chat"},
        {"name": "command-r-plus", "size": "n/a", "speed": "fast", "type": "chat"},
    ],
}


def get_models(provider: str):
    return MODEL_REGISTRY.get(provider, [])
