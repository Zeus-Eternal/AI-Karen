"""Desktop automation helpers."""

import time
import pyautogui

class DesktopAgent:
    """Simple automation agent using PyAutoGUI."""

    def open_app(self, app_name: str) -> None:
        """Open an application by name using the OS start menu."""
        pyautogui.press("winleft")
        time.sleep(1)
        pyautogui.typewrite(app_name)
        time.sleep(1)
        pyautogui.press("enter")

    def type_text(self, text: str) -> None:
        """Type ``text`` into the active window."""
        pyautogui.typewrite(text)

    def screenshot(self, path: str = "screenshot.png") -> str:
        """Take a screenshot and return the file path."""
        pyautogui.screenshot(path)
        return path
