def build_degraded_response(requested_provider: str, reason: str) -> str:
    return f'Requested provider: {requested_provider}\nCause: {reason}'
