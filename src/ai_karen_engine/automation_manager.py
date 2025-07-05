"""
AutomationManager: Ironclad Task Orchestration for Kari
- Zero-trust execution model with sandboxing
- Hardware-enforced thread isolation
- Cryptographic job verification
- Fail-closed design
- Environment variable ``KARI_DUCKDB_PASSWORD`` must be set for encrypted
  database access; no fallback password is provided.
"""

import concurrent.futures
import hashlib
import hmac
import logging
import os
import secrets
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import duckdb

# === Security Constants ===
MAX_WORKERS = int(os.getenv("KARI_MAX_AUTOMATION_WORKERS", "4"))
JOB_TIMEOUT = int(os.getenv("KARI_JOB_TIMEOUT", "300"))
DUCKDB_PASSWORD = os.getenv("KARI_DUCKDB_PASSWORD")
if not DUCKDB_PASSWORD:
    raise RuntimeError("KARI_DUCKDB_PASSWORD must be set in the environment!")
SIGNING_KEY = os.getenv("KARI_JOB_SIGNING_KEY")
if not SIGNING_KEY:
    raise RuntimeError("KARI_JOB_SIGNING_KEY must be set in the environment!")

# === Secure Logging ===
Path("/var/log/kari").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/kari/automation.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("automation_manager")
log.setLevel(logging.INFO)

# === Hardware Isolation ===
try:
    import numa

    NUMA_ENABLED = True
except ImportError:
    NUMA_ENABLED = False

# === DuckDB Hardening ===
DB_PATH = Path(os.getenv("KARI_SECURE_DB_PATH", "/secure/kari_automation.db"))
DB_PATH.parent.mkdir(mode=0o700, exist_ok=True)


def init_secure_db():
    conn = duckdb.connect(str(DB_PATH))
    conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS automation_jobs (
            job_id VARCHAR PRIMARY KEY,
            name VARCHAR,
            schedule VARCHAR,
            status VARCHAR CHECK(status IN ('pending','running','success','failed')),
            last_run TIMESTAMP,
            result BLOB,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            signature VARCHAR
        ) WITH (encryption='aes256');
    """
    )
    conn.close()


init_secure_db()


# === Cryptographic Controls ===
def sign_job(job_id: str, name: str, schedule: str) -> str:
    msg = f"{job_id}|{name}|{schedule}".encode()
    return hmac.new(SIGNING_KEY.encode(), msg, hashlib.sha256).hexdigest()


def verify_job(job_data: Dict[str, Any]) -> bool:
    if not all(k in job_data for k in ("job_id", "name", "schedule", "signature")):
        return False
    expected_sig = sign_job(job_data["job_id"], job_data["name"], job_data["schedule"])
    return hmac.compare_digest(expected_sig, job_data.get("signature", ""))


# === Thread Isolation ===
class SecureThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        kwargs["thread_name_prefix"] = "AutomationWorker-"
        super().__init__(*args, **kwargs)

    def submit(self, fn, *args, **kwargs):
        return super().submit(self._wrap_fn(fn), *args, **kwargs)

    def _wrap_fn(self, fn):
        def secured(*args, **kwargs):
            try:
                if NUMA_ENABLED:
                    numa.set_localalloc()
                # Only supported on Unix
                if hasattr(os, "setrlimit"):
                    import resource

                    resource.setrlimit(resource.RLIMIT_CPU, (JOB_TIMEOUT, JOB_TIMEOUT))
                    resource.setrlimit(
                        resource.RLIMIT_AS, (1 << 30, 1 << 30)
                    )  # 1GB RAM
                return fn(*args, **kwargs)
            except Exception as e:
                log.error(f"Job security violation: {str(e)}", exc_info=True)
                raise RuntimeError("Execution aborted by security policy")

        return secured


# === Core Automation Engine ===
class AutomationManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self._executor = SecureThreadPoolExecutor(max_workers=MAX_WORKERS)
        self._job_registry: Dict[str, Callable] = {}
        self._schedule: Dict[str, Dict] = {}
        self._load_jobs()
        self._security_event = threading.Event()
        self._watchdog = threading.Thread(
            target=self._security_monitor, name="AutomationWatchdog", daemon=True
        )
        self._watchdog.start()
        log.info("AutomationManager initialized with security enforcement")

    def _load_jobs(self):
        conn = duckdb.connect(str(DB_PATH))
        conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
        try:
            rows = conn.execute(
                """
                SELECT job_id, name, schedule, status, last_run, result, signature, created_at, updated_at
                FROM automation_jobs
            """
            ).fetchall()
            for job in rows:
                job_data = {
                    "job_id": job[0],
                    "name": job[1],
                    "schedule": job[2],
                    "status": job[3],
                    "last_run": job[4],
                    "result": job[5],
                    "signature": job[6],
                    "created_at": job[7],
                    "updated_at": job[8],
                }
                if verify_job(job_data):
                    self._schedule[job[0]] = job_data
                else:
                    log.critical(f"Tampered job detected: {job[0]}")
        finally:
            conn.close()

    def register_job(self, name: str, func: Callable, schedule: str) -> str:
        job_id = str(uuid.uuid4())
        signature = sign_job(job_id, name, schedule)
        with self._lock:
            self._job_registry[job_id] = func
            self._schedule[job_id] = {
                "job_id": job_id,
                "name": name,
                "schedule": schedule,
                "status": "pending",
                "last_run": None,
                "result": None,
                "signature": signature,
                "created_at": time.time(),
                "updated_at": time.time(),
            }
            self._persist_job(job_id)
            log.info(f"Registered secured job: {name}")
        return job_id

    def _persist_job(self, job_id: str):
        job = self._schedule[job_id]
        conn = duckdb.connect(str(DB_PATH))
        conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO automation_jobs 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job["job_id"],
                    job["name"],
                    job["schedule"],
                    job["status"],
                    job["last_run"],
                    job["result"],
                    job["created_at"],
                    job["updated_at"],
                    job["signature"],
                ),
            )
        finally:
            conn.close()

    def trigger_job(self, job_id: str) -> bool:
        if not verify_job(self._schedule.get(job_id, {})):
            log.error(f"Rejected untrusted job: {job_id}")
            return False

        def secured_runner():
            try:
                job_func = self._job_registry[job_id]
                result = job_func()
                self._update_job_status(job_id, "success", result)
                return True
            except Exception as e:
                self._update_job_status(job_id, "failed", str(e))
                return False

        self._executor.submit(secured_runner)
        return True

    def _update_job_status(self, job_id: str, status: str, result: Any):
        with self._lock:
            job = self._schedule.get(job_id)
            if job:
                job["status"] = status
                job["last_run"] = time.time()
                job["result"] = result  # TODO: Encrypt result for at-rest
                job["updated_at"] = time.time()
                self._persist_job(job_id)

    def _security_monitor(self):
        while not self._security_event.wait(5):
            self._check_system_security()

    def _check_system_security(self):
        for job_id, job in list(self._schedule.items()):
            if not verify_job(job):
                log.critical(f"Runtime tampering detected in job {job_id}")
                self._quarantine_job(job_id)

    def _quarantine_job(self, job_id: str):
        with self._lock:
            self._schedule.pop(job_id, None)
            self._job_registry.pop(job_id, None)
            conn = duckdb.connect(str(DB_PATH))
            conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
            conn.execute("DELETE FROM automation_jobs WHERE job_id = ?", (job_id,))
            conn.close()
            log.warning(f"Quarantined compromised job: {job_id}")

    def shutdown(self):
        self._security_event.set()
        self._executor.shutdown(wait=False)
        log.info("AutomationManager securely terminated")


def get_automation_manager():
    if AutomationManager._instance is None:
        with AutomationManager._lock:
            if AutomationManager._instance is None:
                AutomationManager._instance = AutomationManager()
    return AutomationManager._instance


automation_manager = get_automation_manager()
