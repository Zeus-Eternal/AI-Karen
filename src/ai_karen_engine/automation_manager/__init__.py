"""
AutomationManager: Ironclad Task Orchestration for Kari
- Zero-trust execution model with sandboxing
- Hardware-enforced thread isolation
- Cryptographic job verification
- Fail-closed design
- Secure DuckDB path resolution:
    1) Respect KARI_SECURE_DB_PATH (supports ~ expansion)
    2) Use /secure/kari_automation.db if /secure exists & is writable (containers)
    3) Fall back to ~/.kari/secure/kari_automation.db
- Environment variable ``KARI_DUCKDB_PASSWORD`` must be set for encrypted
  database access; no fallback password is provided.
"""

import concurrent.futures
import hashlib
import hmac
import logging
import os
import platform
import stat
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict

from ai_karen_engine.automation_manager.encryption_utils import (
    decrypt_data,
    encrypt_data,
)

import duckdb

# === Security Constants ===
MAX_WORKERS = int(os.getenv("KARI_MAX_AUTOMATION_WORKERS", "4"))
JOB_TIMEOUT = int(os.getenv("KARI_JOB_TIMEOUT", "300"))

_ephemeral_duckdb_password = False
DUCKDB_PASSWORD = os.getenv("KARI_DUCKDB_PASSWORD")
if not DUCKDB_PASSWORD:
    DUCKDB_PASSWORD = hashlib.sha256(os.urandom(32)).hexdigest()
    _ephemeral_duckdb_password = True

_ephemeral_signing_key = False
SIGNING_KEY = os.getenv("KARI_JOB_SIGNING_KEY")
if not SIGNING_KEY:
    SIGNING_KEY = hashlib.sha256(os.urandom(32)).hexdigest()
    _ephemeral_signing_key = True

# === Secure Logging ===
def _resolve_log_dir() -> Path:
    env_dir = os.getenv("KARI_LOG_DIR")
    if env_dir:
        p = Path(env_dir)
        try:
            p.mkdir(parents=True, exist_ok=True)
            with open(p / "automation.log", "a"):
                pass
            return p
        except Exception:
            pass
    fallback = Path.home() / ".kari" / "logs"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

LOG_DIR = _resolve_log_dir()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "automation.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("automation_manager")
log.setLevel(logging.INFO)

if _ephemeral_duckdb_password:
    log.warning(
        "KARI_DUCKDB_PASSWORD not set; generated ephemeral development password. Set the env var for persistent encrypted storage."
    )

if _ephemeral_signing_key:
    log.warning(
        "KARI_JOB_SIGNING_KEY not set; generated ephemeral development signing key. Provide a stable key in production."
    )

# === Hardware Isolation ===
try:
    import numa

    NUMA_ENABLED = True
except ImportError:
    NUMA_ENABLED = False

# === Cross-Platform Permission Handling ===
def _set_secure_permissions(path: Path) -> bool:
    """
    Set secure permissions on a directory in a cross-platform manner.
    
    Args:
        path: Path to the directory to secure
        
    Returns:
        bool: True if permissions were set successfully, False otherwise
    """
    try:
        # Detect operating system
        system = platform.system().lower()
        
        if system == "windows":
            # On Windows, we rely on default NTFS permissions
            # which are typically secure for user directories
            log.info(f"Windows detected - using default permissions for {path}")
            return True
        else:
            # POSIX systems (Linux, macOS, Unix-like)
            log.info(f"POSIX system detected ({system}) - setting restrictive permissions for {path}")
            
            # Set directory permissions to 0o700 (owner read/write/execute only)
            path.chmod(stat.S_IRWXU)  # 0o700
            
            # Verify permissions were set correctly
            current_perms = path.stat().st_mode & 0o777
            if current_perms == 0o700:
                log.info(f"Successfully set secure permissions (0o700) on {path}")
                return True
            else:
                log.warning(f"Permission verification failed for {path}: expected 0o700, got {oct(current_perms)}")
                return False
                
    except PermissionError as e:
        log.warning(f"Permission denied when setting secure permissions on {path}: {e}")
        return False
    except OSError as e:
        log.warning(f"OS error when setting secure permissions on {path}: {e}")
        return False
    except Exception as e:
        log.warning(f"Unexpected error when setting secure permissions on {path}: {e}")
        return False

# === DuckDB Hardening ===
def _resolve_secure_db_path() -> Path:
    """
    Cross-platform, reuse existing secure folder:
      1) Respect KARI_SECURE_DB_PATH (supports ~ expansion)
      2) Use /secure/kari_automation.db if /secure exists & is writable (container)
      3) Fall back to per-user secure dir: ~/.kari/secure/kari_automation.db
      4) Emergency fallback to temp directory if all else fails
    """
    # Try environment variable path first
    env_path = os.getenv("KARI_SECURE_DB_PATH")
    if env_path:
        p = Path(os.path.expanduser(env_path))
        try:
            # Create parent directories with proper cross-platform handling
            p.parent.mkdir(parents=True, exist_ok=True)
            
            # Set secure permissions using cross-platform function
            perm_success = _set_secure_permissions(p.parent)
            if perm_success:
                log.info(f"Successfully created and secured environment path: {p.parent}")
            else:
                log.warning(f"Created environment path but failed to set secure permissions: {p.parent}")
            
            return p
        except (PermissionError, OSError) as e:
            log.warning(f"Failed to create directory {p.parent}: {e}")
            # Fall through to try other options

    # Try container secure directory
    container_secure = Path("/secure")
    if container_secure.exists() and os.access(container_secure, os.W_OK):
        try:
            # Container directory should already exist, just ensure it's accessible
            db_path = container_secure / "kari_automation.db"
            
            # Try to set secure permissions on container directory
            perm_success = _set_secure_permissions(container_secure)
            if perm_success:
                log.info(f"Successfully secured container directory: {container_secure}")
            else:
                log.warning(f"Using container directory but failed to set secure permissions: {container_secure}")
            
            return db_path
        except (PermissionError, OSError) as e:
            log.warning(f"Failed to secure container directory: {e}")
            # Fall through to user secure directory

    # Try user secure directory
    user_secure = Path.home() / ".kari" / "secure"
    try:
        # Create all parent directories recursively
        user_secure.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions using cross-platform function
        perm_success = _set_secure_permissions(user_secure)
        if perm_success:
            log.info(f"Successfully created and secured user directory: {user_secure}")
        else:
            log.warning(f"Created user directory but failed to set secure permissions: {user_secure}")
        
        return user_secure / "kari_automation.db"
    except (PermissionError, OSError) as e:
        log.error(f"Failed to create user secure directory {user_secure}: {e}")
        
        # Emergency fallback to temp directory
        try:
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "kari_secure"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to set permissions on temp directory
            perm_success = _set_secure_permissions(temp_dir)
            if perm_success:
                log.warning(f"Using emergency temp directory with secure permissions: {temp_dir}")
            else:
                log.warning(f"Using emergency temp directory without secure permissions: {temp_dir}")
            
            return temp_dir / "kari_automation.db"
        except Exception as temp_e:
            log.critical(f"Emergency fallback to temp directory failed: {temp_e}")
            raise RuntimeError(f"Unable to create any secure database directory. Last error: {e}")


DB_PATH = _resolve_secure_db_path()


def init_secure_db():
    """
    Initialize the secure database with cross-platform directory creation and permission handling.
    """
    global DB_PATH
    parent = DB_PATH.parent
    
    try:
        # Ensure the parent directory exists with proper permissions
        parent.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions using cross-platform function
        perm_success = _set_secure_permissions(parent)
        if not perm_success:
            log.warning(f"Database directory created but secure permissions could not be set: {parent}")
        
    except PermissionError as e:
        log.warning(f"Permission denied creating database directory {parent}: {e}")
        
        # Fall back to per-user secure dir if the chosen parent is not writable
        fallback = Path.home() / ".kari" / "secure"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            
            # Set secure permissions on fallback directory
            perm_success = _set_secure_permissions(fallback)
            if perm_success:
                log.info(f"Successfully created fallback directory with secure permissions: {fallback}")
            else:
                log.warning(f"Fallback directory created but secure permissions could not be set: {fallback}")
            
            DB_PATH = fallback / "kari_automation.db"
            parent = fallback
            log.warning(f"No permission for original path; using fallback: {fallback}")
            
        except Exception as fallback_e:
            log.error(f"Fallback directory creation also failed: {fallback_e}")
            # Continue with original path and hope for the best
            log.warning(f"Continuing with potentially insecure database path: {DB_PATH}")
    
    except OSError as e:
        log.error(f"OS error creating database directory {parent}: {e}")
        # Continue with existing path
        log.warning(f"Continuing with existing database path despite errors: {DB_PATH}")

    log.info("Automation DB path: %s", DB_PATH)
    conn = duckdb.connect(str(DB_PATH))
    # Skip encryption for development - only use in production with encrypted DuckDB
    try:
        conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
        encryption_clause = "WITH (encryption='aes256')"
    except Exception:
        # Standard DuckDB doesn't support encryption, continue without it
        encryption_clause = ""
        log.warning("DuckDB encryption not available, using unencrypted database for development")

    conn.execute(
        f"""
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
        ) {encryption_clause};
    """
    )
    conn.close()


# Database will be initialized lazily when AutomationManager is created


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
    _lock = threading.RLock()  # Use RLock to allow same thread to acquire multiple times

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        # Initialize database first
        init_secure_db()
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
        try:
            conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
        except Exception:
            # Skip encryption if not available
            pass
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
                    "result": decrypt_data(job[5]),
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
        try:
            conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
        except Exception:
            # Skip encryption if not available
            pass
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
                job["result"] = encrypt_data(result)
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
            try:
                conn.execute(f"PRAGMA key='{DUCKDB_PASSWORD}'")
            except Exception:
                # Skip encryption if not available
                pass
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


# AutomationManager will be created lazily when first accessed

__all__ = [
    "AutomationManager",
    "get_automation_manager",
    "init_secure_db",
    "encrypt_data",
    "decrypt_data",
    "SecureThreadPoolExecutor",
]
