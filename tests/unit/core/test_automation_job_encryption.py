import importlib
import time

import duckdb
from cryptography.fernet import Fernet


def test_job_result_encrypted(tmp_path, monkeypatch):
    db = tmp_path / "automation.db"
    monkeypatch.setenv("KARI_SECURE_DB_PATH", str(db))
    monkeypatch.setenv("KARI_DUCKDB_PASSWORD", "pw")
    monkeypatch.setenv("KARI_JOB_SIGNING_KEY", "sign")
    monkeypatch.setenv("KARI_JOB_ENC_KEY", Fernet.generate_key().decode())

    import ai_karen_engine.automation_manager as am

    importlib.reload(am)

    mgr = am.get_automation_manager()

    def hello():
        return "secret"

    jid = mgr.register_job("hello", hello, "now")
    mgr.trigger_job(jid)
    time.sleep(0.1)

    conn = duckdb.connect(str(db))
    conn.execute("PRAGMA key='pw'")
    stored = conn.execute(
        "SELECT result FROM automation_jobs WHERE job_id=?", (jid,)
    ).fetchone()[0]
    conn.close()

    assert stored != b"secret"
    assert am.decrypt_data(stored) == "secret"
    mgr.shutdown()
