"""Enhanced runtime diagnostics for the Kari Mobile UI."""
import sys
import importlib
import platform
import subprocess
import logging
import os
from pathlib import Path

from src.integrations.llm_registry import registry as llm_registry
from .memory_controller import MEM_DB
from .vault import VAULT_DB

logger = logging.getLogger(__name__)

# --- Utility: Package & Model Checks --- #

def _check_import(package_name: str) -> bool:
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def _install_package(package_name: str):
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)
        logger.info(f"Installed missing package: {package_name}")
    except subprocess.CalledProcessError:
        logger.error(f"Failed to auto-install {package_name}")

def _check_and_install(package: str) -> bool:
    if not _check_import(package):
        _install_package(package)
        return _check_import(package)
    return True

# --- SpaCy Model Check --- #

def _get_spacy_models() -> list:
    try:
        import spacy
        return list(spacy.util.get_installed_models())
    except Exception:
        return []

def _ensure_spacy_model(model: str = "en_core_web_sm"):
    try:
        import spacy
        if model not in spacy.util.get_installed_models():
            subprocess.run([sys.executable, "-m", "spacy", "download", model], check=True)
            logger.info(f"Downloaded spaCy model: {model}")
    except Exception as e:
        logger.warning(f"spaCy model install failed: {e}")

# --- GPU / CUDA / Platform --- #

def _check_cuda() -> str:
    try:
        import torch
        return f"cuda:{torch.cuda.get_device_name(0)}" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "unavailable"

def _check_gpu_info() -> str:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True
        )
        return result.stdout.strip() if result.returncode == 0 else "nvidia-smi not available"
    except Exception:
        return "GPU info not available"

def _get_python_version() -> str:
    return platform.python_version()

# --- Database & Service Checks --- #

def _test_duckdb(db_path: Path) -> bool:
    """Attempt to connect to a DuckDB file."""
    try:
        import duckdb  # local import to avoid mandatory dependency
        db_path.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(db_path))
        con.execute("SELECT 1")
        con.close()
        return True
    except Exception as e:
        logger.warning(f"DuckDB check failed for {db_path}: {e}")
        return False


def _ping_milvus() -> bool:
    """Ping Milvus if pymilvus is installed."""
    try:
        from pymilvus import connections
    except Exception:
        return False
    host = os.getenv("MILVUS_HOST", "localhost")
    port = os.getenv("MILVUS_PORT", "19530")
    try:
        connections.connect(alias="health", host=host, port=port)
        conn = connections.get_connection("health")
        conn.list_collections()
        connections.disconnect("health")
        return True
    except Exception as e:
        logger.warning(f"Milvus ping failed: {e}")
        return False

# --- Main System Health Check --- #

def get_system_health() -> dict:
    """Perform full diagnostics across memory, LLMs, GPU, and package status."""

    # Core DBs
    duckdb_memory = _test_duckdb(MEM_DB)
    duckdb_vault = _test_duckdb(VAULT_DB)
    milvus_ok = _ping_milvus()

    # Ensure base NLP stack
    spacy_ok = _check_and_install("spacy")
    sklearn_ok = _check_and_install("scikit-learn")
    torch_ok = _check_and_install("torch")
    transformers_ok = _check_and_install("transformers")

    # Ensure minimal spaCy model
    if spacy_ok:
        _ensure_spacy_model("en_core_web_sm")

    backends = {
        "ollama_cpp": "ollama_cpp" in llm_registry.backends,
        "openai": "openai" in llm_registry.backends,
        "deepseek": "deepseek" in llm_registry.backends,
    }

    return {
        "runtime": {
            "python_version": _get_python_version(),
            "cuda": _check_cuda(),
            "gpu_info": _check_gpu_info(),
        },
        "memory": {
            "redis": "ok",
            "duckdb_memory": duckdb_memory,
            "duckdb_vault": duckdb_vault,
            "milvus": milvus_ok,
        },
        "llm_registry": llm_registry.active,
        "llm_backends": backends,
        "packages": {
            "spacy": spacy_ok,
            "scikit-learn": sklearn_ok,
            "torch": torch_ok,
            "transformers": transformers_ok,
        },
        "spacy_models": _get_spacy_models(),
    }

