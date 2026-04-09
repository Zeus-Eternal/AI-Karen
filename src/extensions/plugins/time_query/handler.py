from datetime import datetime, timezone

async def run(_params: dict) -> str:
    """Return the current UTC time."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
