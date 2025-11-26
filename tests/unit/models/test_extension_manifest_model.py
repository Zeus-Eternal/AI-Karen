from ai_karen_engine.extension_host.models2 import ExtensionManifest


def test_extension_manifest_valid():
    manifest = ExtensionManifest(
        name="test-extension",
        version="1.0.0",
        display_name="Test Extension",
        description="A test extension",
        author="Author",
        license="MIT",
        category="test",
    )
    assert manifest.name == "test-extension"
