class LLMUtils:
    """Tiny placeholder for local language model interactions."""

    def __init__(self):
        self.counter = 0

    def generate_text(self, prompt: str) -> str:
        if "Break this goal" in prompt:
            return "step1; step2; step3"
        self.counter += 1
        if self.counter >= 3:
            return "DONE"
        return f"auto_subtask_{self.counter}"
