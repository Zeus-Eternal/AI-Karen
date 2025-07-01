MODEL_REGISTRY = {
    "Local (Ollama)": [
        {"name": "llama3.2:latest", "size": "7B", "speed": "fast", "type": "chat"},
        {"name": "mistral", "size": "7B", "speed": "fast", "type": "chat"},
        {"name": "codellama", "size": "7B", "speed": "fast", "type": "code"},
    ],
    "HuggingFace": [
        {"name": "gpt2", "size": "small", "speed": "fast", "type": "chat"},
        {"name": "bloom", "size": "176B", "speed": "slow", "type": "chat"},
        {"name": "falcon-7b", "size": "7B", "speed": "medium", "type": "chat"},
    ],
    "Groq": [
        {"name": "llama3-70b", "size": "70B", "speed": "fast", "type": "chat"},
        {"name": "mixtral-8x7b", "size": "56B", "speed": "fast", "type": "chat"},
    ],
}


def get_models(provider: str):
    return MODEL_REGISTRY.get(provider, [])
