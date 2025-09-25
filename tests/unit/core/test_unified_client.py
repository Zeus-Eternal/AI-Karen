from core.response.unified_client import UnifiedLLMClient


class DummyLLM:
    def __init__(self, response: str, fail: bool = False) -> None:
        self.response = response
        self.fail = fail
        self.calls = 0
        self.last_kwargs: dict[str, object] | None = None

    def generate(self, prompt: str, **kwargs: object) -> str:
        self.calls += 1
        self.last_kwargs = kwargs
        if self.fail:
            raise RuntimeError("fail")
        return self.response


def test_local_used_first() -> None:
    local = DummyLLM("local")
    remote = DummyLLM("remote")
    client = UnifiedLLMClient(local_client=local, remote_client=remote, default_model="test-model")
    assert client.generate("hi") == "local"
    assert local.calls == 1 and remote.calls == 0
    assert local.last_kwargs is not None and local.last_kwargs.get("model") == "test-model"


def test_remote_used_when_local_fails() -> None:
    local = DummyLLM("local", fail=True)
    remote = DummyLLM("remote")
    client = UnifiedLLMClient(local, remote)
    assert client.generate("hi") == "remote"
    assert local.calls == 1 and remote.calls == 1


def test_fallback_when_all_fail() -> None:
    local = DummyLLM("local", fail=True)
    remote = DummyLLM("remote", fail=True)
    client = UnifiedLLMClient(local, remote)
    assert client.generate("hi") == "No providers available"
