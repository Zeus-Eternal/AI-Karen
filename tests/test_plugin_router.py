from core.plugin_router import PluginRouter


def test_load_plugin():
    router = PluginRouter()
    plugin = router.get_plugin("greet")
    assert plugin is not None
    assert callable(plugin.handler)
    assert "required_roles" in plugin.manifest


def test_invalid_manifest(monkeypatch, tmp_path):
    bad = tmp_path / "bad_plugin"
    bad.mkdir()
    (bad / "plugin_manifest.json").write_text("{ invalid json }")
    monkeypatch.setattr("core.plugin_router.PLUGIN_DIR", str(tmp_path))
    router = PluginRouter()
    assert not router.intent_map
