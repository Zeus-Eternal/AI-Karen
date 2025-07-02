import json
from mobile_ui.logic import model_registry as mr


def test_load_registry(tmp_path, monkeypatch):
    data = {"foo": {"model_name": "foo", "provider": "llama-cpp"}}
    path = tmp_path / "reg.json"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(mr, "REGISTRY_PATH", path)
    assert mr.load_registry() == data


def test_get_registry_models_filter(tmp_path, monkeypatch):
    data = {
        "foo": {"model_name": "foo", "provider": "llama-cpp"},
        "bar": {"model_name": "bar", "provider": "anthropic"},
    }
    path = tmp_path / "reg.json"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(mr, "REGISTRY_PATH", path)
    all_models = mr.get_registry_models()
    assert len(all_models) == 2
    llama_only = mr.get_registry_models("local")  # alias canonicalized
    assert len(llama_only) == 1
    assert llama_only[0]["model_name"] == "foo"


def test_get_models_alias(monkeypatch):
    monkeypatch.setitem(mr.MODEL_PROVIDERS, "llama-cpp", lambda: ["m1"])
    assert mr.get_models("ollama") == ["m1"]
