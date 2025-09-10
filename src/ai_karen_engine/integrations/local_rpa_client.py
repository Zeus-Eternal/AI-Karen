
# Avoid importing pyautogui at module import time. In headless containers
# importing pyautogui can trigger modules (like mouseinfo) that access
# DISPLAY and raise KeyError. Use a lazy importer and cache the result.
_pyautogui = None
_pyautogui_checked = False


def _get_pyautogui():
    """Lazily import pyautogui and cache the result.

    Returns None if the library is unavailable or cannot be used in the
    current environment (e.g., headless container without DISPLAY).
    """
    global _pyautogui, _pyautogui_checked
    if _pyautogui_checked:
        return _pyautogui

    try:
        # Import inside the function to avoid side-effects at module import
        # time. Catch broad exceptions because some GUI libraries raise
        # KeyError or other errors when DISPLAY is missing.
        import pyautogui as _pa  # type: ignore
        _pyautogui = _pa
    except Exception:
        _pyautogui = None
    _pyautogui_checked = True
    return _pyautogui


class LocalRPAClient:
    """Thin wrapper around PyAutoGUI for local RPA tasks.

    This class will silently no-op if pyautogui isn't available or usable.
    """

    def click(self, x: int, y: int) -> None:
        pyautogui = _get_pyautogui()
        if pyautogui is None:
            return None
        pyautogui.click(x, y)

    def type_text(self, text: str) -> None:
        pyautogui = _get_pyautogui()
        if pyautogui is None:
            return None
        # use typewrite for compatibility with older pyautogui versions
        pyautogui.typewrite(text)

    def screenshot(self, path: str = "screenshot.png") -> str:
        pyautogui = _get_pyautogui()
        if pyautogui is None:
            return path
        pyautogui.screenshot(path)
        return path

