from ..src.ai_karen_engine.echocore.echo_vault import EchoVault
from ..src.ai_karen_engine.echocore.dark_tracker import DarkTracker


def test_vault_backup_restore(tmp_path):
    vault = EchoVault("user", base_dir=tmp_path)
    vault.backup({"foo": "bar"})
    data = vault.restore()
    assert data["foo"] == "bar"


def test_dark_tracker_capture(tmp_path):
    tracker = DarkTracker("user", base_dir=tmp_path)
    tracker.capture({"event": "x"})
    log_file = tmp_path / "user" / "dark.log"
    assert log_file.exists()
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1 and "event" in lines[0]
