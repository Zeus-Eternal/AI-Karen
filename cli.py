import argparse
import json
import sys
from pathlib import Path

from src.ai_karen_engine import LLMOrchestrator
from ai_karen_engine.plugin_router import PluginRouter


CONFIG_PATH = Path("config") / "settings.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def self_test() -> None:
    cfg = load_config()

    # ensure optional dependencies don't block plugin loading during tests
    for dep in ["pyautogui", "urwid"]:
        if dep not in sys.modules:
            sys.modules[dep] = type(sys)(dep)

    orchestrator = LLMOrchestrator()
    router = PluginRouter()

    summary = {
        "provider": cfg.get("provider", "unknown"),
        "model": cfg.get("model", "unknown"),
        "plugins": len(router.list_intents()),
        "active_llm": getattr(orchestrator.default_llm, "__class__", type("", (object,), {}))
        .__name__,
    }
    print("Self test summary:")
    for k, v in summary.items():
        print(f"{k}: {v}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Kari command line utilities")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="load configuration and validate plugins",
    )
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
