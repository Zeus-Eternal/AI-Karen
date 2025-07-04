"""
Kari Tauri Launcher Skeleton
- Loads page manifest and dispatches pages using ui_core
- Actual Tauri window spawning is delegated to the Rust project
"""
import logging
import subprocess
from pathlib import Path

from src.ui_logic import ui_core
from ui_launchers.tauri_launcher.helpers.session import get_user_context


def main() -> None:
    """Entry point for the Tauri desktop launcher."""
    logging.basicConfig(level=logging.INFO)
    user_ctx = get_user_context()
    manifest = ui_core.get_page_manifest(user_ctx)
    logging.info("Available pages: %s", [p["label"] for p in manifest])
    if manifest:
        try:
            ui_core.dispatch_page(manifest[0]["key"], user_ctx)
        except NotImplementedError:
            logging.info("Page stub executed")
    else:
        logging.warning("No accessible pages for current user")

    tauri_dir = Path(__file__).parent
    if (tauri_dir / "src-tauri").exists():
        try:
            subprocess.run(["tauri", "dev"], cwd=tauri_dir, check=False)
        except Exception as exc:
            logging.error("Failed to start Tauri: %s", exc)


if __name__ == "__main__":
    main()
