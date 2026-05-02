from __future__ import annotations

def supports_general_chat(capabilities: list[str]) -> bool:
    blocked = {'code_only', 'embedding_only'}
    return not any(cap in blocked for cap in capabilities)
