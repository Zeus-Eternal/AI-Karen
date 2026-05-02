def sanitize_response_text(text: str) -> str:
    return text.replace('[transformers:auto]', '').strip()
