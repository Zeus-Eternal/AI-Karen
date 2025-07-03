try:
    import pyautogui
except ModuleNotFoundError:  # pragma: no cover - fallback when library missing
    pyautogui = None


class LocalRPAClient:
    """Thin wrapper around PyAutoGUI for local RPA tasks."""

    def click(self, x: int, y: int) -> None:
        if pyautogui is None:
            return None
        pyautogui.click(x, y)

    def type_text(self, text: str) -> None:
        if pyautogui is None:
            return None
        pyautogui.typewrite(text)

    def screenshot(self, path: str = "screenshot.png") -> str:
        if pyautogui is None:
            return path
        pyautogui.screenshot(path)
        return path

