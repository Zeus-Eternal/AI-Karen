from .agent import DesktopAgent

async def run(params: dict) -> dict:
    """Entry point for the desktop automation plugin."""
    agent = DesktopAgent()
    action = params.get("action")
    target = params.get("target")

    if action == "open_app":
        agent.open_app(str(target))
        return {"status": f"Opened {target}"}
    elif action == "type_text":
        agent.type_text(str(target))
        return {"status": f"Typed text: {target}"}
    elif action == "screenshot":
        path = agent.screenshot()
        return {"status": f"Screenshot saved to {path}"}
    else:
        return {"error": "Unknown action"}
