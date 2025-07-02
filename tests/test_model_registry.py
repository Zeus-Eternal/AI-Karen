import json
from ui.mobile_ui.services import model_registry as mr


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


def test_get_models_reads_registry(tmp_path, monkeypatch):
    data = {
        "foo": {"model_name": "foo", "provider": "llama-cpp"},
        "bar": {"model_name": "bar", "provider": "custom_provider"},
    }
    path = tmp_path / "reg.json"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(mr, "REGISTRY_PATH", path)
    models = mr.get_models()
    assert any(m["model_name"] == "foo" for m in models)
    assert any(m["provider"] == "custom_provider" for m in models)


def test_ready_models_default(tmp_path, monkeypatch):
    path = tmp_path / "reg.json"
    path.write_text("{}")
    monkeypatch.setattr(mr, "REGISTRY_PATH", path)
    ready = mr.get_ready_models()
    assert any(m["model_name"] == "distilbert-base-uncased" for m in ready)


def test_get_providers_includes_registry_providers(tmp_path, monkeypatch):
    data = {
        "foo": {"model_name": "foo", "provider": "llama-cpp"},
        "bar": {"model_name": "bar", "provider": "custom_provider"},
    }
    path = tmp_path / "reg.json"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(mr, "REGISTRY_PATH", path)
    providers = mr.get_providers()
    assert "llama-cpp" in providers
    assert "custom_provider" in providers
