import importlib
from ui_logic.config import feature_flags


def test_env_override(monkeypatch):
    key = "enable_iot"
    env_var = "KARI_FEATURE_ENABLE_IOT"
    monkeypatch.delenv(env_var, raising=False)
    importlib.reload(feature_flags)
    assert feature_flags.is_feature_enabled(key) is False

    monkeypatch.setenv(env_var, "true")
    assert feature_flags.is_feature_enabled(key)

    monkeypatch.setenv(env_var, "0")
    assert not feature_flags.is_feature_enabled(key)

