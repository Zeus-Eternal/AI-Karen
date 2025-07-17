class Llama:
    def __init__(self, *args, **kwargs):
        pass

    def create_completion(self, prompt, stream=False, **kwargs):
        if stream:
            for ch in ["a", "b"]:
                yield {"choices": [{"text": ch}]}
        else:
            return {"choices": [{"text": "ok"}]}

    def embed(self, text):
        return [0.0]
