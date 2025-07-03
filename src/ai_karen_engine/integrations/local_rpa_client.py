import pyautogui


class LocalRPAClient:
    """Thin wrapper around PyAutoGUI for local RPA tasks."""

    def click(self, x: int, y: int) -> None:
        pyautogui.click(x, y)

    def type_text(self, text: str) -> None:
        pyautogui.typewrite(text)

    def screenshot(self, path: str = "screenshot.png") -> str:
        pyautogui.screenshot(path)
        return path

