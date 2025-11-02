"""Desktop automation helpers."""

import time

_pyautogui = None
_pyautogui_checked = False


def _get_pyautogui():
    global _pyautogui, _pyautogui_checked
    if _pyautogui_checked:
        return _pyautogui
    try:
        import pyautogui as _pa  # type: ignore
        _pyautogui = _pa
    except Exception:
        _pyautogui = None
    _pyautogui_checked = True
    return _pyautogui


class DesktopAgent:
    """Simple automation agent using PyAutoGUI.

    Methods no-op when pyautogui isn't available (e.g., headless containers).
    """

    def open_app(self, app_name: str) -> None:
        """Open an application by name using the OS start menu."""
        pyautogui = _get_pyautogui()
        if pyautogui is None:
            return None
        pyautogui.press("winleft")
        time.sleep(1)
        pyautogui.typewrite(app_name)
        time.sleep(1)
        pyautogui.press("enter")

    def type_text(self, text: str) -> None:
        """Type ``text`` into the active window."""
        pyautogui = _get_pyautogui()
        if pyautogui is None:
            return None
        pyautogui.typewrite(text)

    def screenshot(self, path: str = "screenshot.png") -> str:
        """Take a screenshot and return the file path."""
        pyautogui = _get_pyautogui()
        if pyautogui is None:
            return path
        pyautogui.screenshot(path)
        return path
