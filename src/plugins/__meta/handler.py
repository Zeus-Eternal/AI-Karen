import json
from pathlib import Path

COMMAND_MANIFEST = Path(__file__).with_name("command_manifest.json")


def _load_commands() -> list:
    try:
        return json.loads(COMMAND_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return []


async def run(params: dict) -> dict:
    """Return available meta commands or details for a specific command."""
    command = params.get("command")
    commands = _load_commands()
    if not command or command == "list":
        return {"commands": commands}

    for cmd in commands:
        if cmd.get("keyword") == command:
            return cmd

    return {"error": "unknown command"}
