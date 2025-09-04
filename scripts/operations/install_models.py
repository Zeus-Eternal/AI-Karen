#!/usr/bin/env python3
"""
Kari Model Manager v2 — HuggingFace Browser, Downloader, and Filesystem Normalizer

- Lists models by org/user; shows detailed metadata & file sizes
- Downloads with include/exclude patterns and resumable cache
- Places artifacts in an OPINIONATED folder layout under ./models
- Maintains a living ./models/llm_registry.json (SSOT)
- Migrates legacy layouts into the new scheme (idempotent)
- Preserves 'ensure_*' helpers (DistilBERT, spaCy, basic sklearn classifier)

Install:
  pip install huggingface_hub==0.25.2 rich==13.7.1 humanfriendly==10.0
  # optional for ensure_basic_classifier:
  pip install scikit-learn==1.4.2 joblib==1.4.2
  # optional for ensure_spacy:
  pip install spacy==3.7.4 && python -m spacy download en_core_web_trf

Usage (examples):
  python model_manager.py migrate
  python model_manager.py list --owner TinyLlama
  python model_manager.py info --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
  python model_manager.py download --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --dest ./models
  python model_manager.py browse --owner TinyLlama --dest ./models/llama-cpp
  python model_manager.py ensure --distilbert --spacy --basic-cls
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Any

# ---------- Soft deps ----------
try:
    from huggingface_hub import HfApi, snapshot_download, model_info
    from huggingface_hub.utils import HfHubHTTPError
except Exception:
    HfApi = None  # type: ignore
    snapshot_download = None  # type: ignore
    model_info = None  # type: ignore

try:
    from rich.console import Console
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import box
except Exception:
    Console = None  # type: ignore
    Table = None  # type: ignore
    Prompt = None  # type: ignore
    Confirm = None  # type: ignore
    box = None  # type: ignore

try:
    from humanfriendly import format_size
except Exception:
    def format_size(n: int) -> str:
        for u in ["B", "KB", "MB", "GB", "TB"]:
            if n < 1024:
                return f"{n:.1f} {u}"
            n //= 1024
        return f"{n:.1f} PB"

try:
    import psutil
except Exception:
    psutil = None  # type: ignore

# ---------- Constants ----------
MODELS_ROOT = Path("../../models")
REGISTRY_PATH = MODELS_ROOT / "model_registry.json"  # Separate from llm_registry.json
CONFIGS_DIR = MODELS_ROOT / "configs"
LLAMACPP_DIR = MODELS_ROOT / "llama-cpp"
TRANSFORMERS_DIR = MODELS_ROOT / "transformers"
DISTILBERT_PIN = MODELS_ROOT / "distilbert-base-uncased"  # backwards-compat

GGUF_PATTERN = re.compile(r"\.gguf(\.tmp|\.part|\.corrupt)?$", re.IGNORECASE)

# Error codes for structured error handling
ERROR_CODES = {
    "E_NET": "Network connectivity issue",
    "E_DISK": "Disk space or I/O issue", 
    "E_PERM": "Permission denied",
    "E_LICENSE": "License acceptance required",
    "E_VERIFY": "Integrity verification failed",
    "E_SCHEMA": "Schema validation failed",
    "E_COMPAT": "Compatibility check failed",
    "E_QUOTA": "Storage quota exceeded",
    "E_ARGS": "Invalid arguments",
    "E_NOT_FOUND": "Model or resource not found"
}

# ---------- Data ----------
@dataclass
class FileEntry:
    path: str
    size: int

@dataclass
class ModelSummary:
    model_id: str
    last_modified: Optional[datetime]
    likes: Optional[int]
    downloads: Optional[int]
    library_name: Optional[str]
    tags: List[str]

@dataclass
class OperationResult:
    success: bool
    message: str
    error_code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class ModelInfo:
    model_id: str
    revision: Optional[str]
    files: List[FileEntry]
    total_size: int
    library: str
    install_path: Optional[str] = None

@dataclass
class CompatibilityInfo:
    cpu_features: List[str]
    gpu_required: bool
    min_ram_gb: float
    min_vram_gb: float
    compatible: bool
    warnings: List[str]

@dataclass
class LicenseInfo:
    license_type: Optional[str]
    requires_acceptance: bool
    license_url: Optional[str]
    accepted_by: Optional[str] = None
    accepted_at: Optional[datetime] = None

# ---------- Console ----------
def console() -> Console:
    if Console is None:
        class _Dummy:
            def print(self, *a, **k): print(*a)
        return _Dummy()  # type: ignore
    return Console()

# Global flags for output and network mode
_json_output = False
_quiet_mode = False
_offline_mode = False
_mirror_url = None

def set_output_mode(json_output: bool = False, quiet: bool = False) -> None:
    global _json_output, _quiet_mode
    _json_output = json_output
    _quiet_mode = quiet

def set_network_mode(offline: bool = False, mirror_url: Optional[str] = None) -> None:
    global _offline_mode, _mirror_url
    _offline_mode = offline
    _mirror_url = mirror_url

def output_result(result: OperationResult) -> None:
    """Output result in appropriate format (JSON or human-readable)"""
    if _json_output:
        output_data = asdict(result)
        # Convert datetime objects to ISO strings for JSON serialization
        if result.data:
            for key, value in result.data.items():
                if isinstance(value, datetime):
                    result.data[key] = value.isoformat()
        print(json.dumps(output_data, indent=2))
    else:
        if result.success:
            if not _quiet_mode:
                console().print(f"[green]Success:[/green] {result.message}")
        else:
            console().print(f"[red]Error ({result.error_code}):[/red] {result.message}")

def bail(msg: str, code: int = 1, error_code: str = "E_ARGS") -> None:
    result = OperationResult(success=False, message=msg, error_code=error_code)
    output_result(result)
    sys.exit(code)

def require_hf() -> None:
    if HfApi is None or snapshot_download is None or model_info is None:
        bail("huggingface_hub is required. pip install huggingface_hub")

def require_rich() -> None:
    if Console is None or Table is None or Prompt is None:
        bail("rich is required. pip install rich")

def validate_mirror_connectivity(mirror_url: str) -> bool:
    """Validate that the mirror URL is accessible"""
    try:
        import urllib.request
        import urllib.error
        import ssl
        
        # Create a context that doesn't verify SSL certificates for testing
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Try to access the mirror URL
        req = urllib.request.Request(mirror_url, headers={'User-Agent': 'model-manager/1.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            return response.status == 200
    except Exception:
        return False

def check_offline_mode() -> None:
    """Check if we're in offline mode and bail if network access is required"""
    if _offline_mode:
        bail("Operation requires network access but --offline mode is enabled", error_code="E_NET")

def human_dt(dt: Optional[datetime]) -> str:
    return "-" if not dt else dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# ---------- Helpers ----------
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def sum_sizes(files: Iterable[FileEntry]) -> int:
    return sum(f.size for f in files)

def parse_owner_repo(model_id: str) -> tuple[str, str]:
    """
    'org/repo' -> ('org','repo'), 'distilbert-base-uncased' -> ('_','distilbert-base-uncased')
    """
    parts = model_id.split("/")
    if len(parts) == 1:
        return "_", parts[0]
    return parts[0], parts[1]

def choose_library(tags: List[str], library_name: Optional[str]) -> str:
    # Prefer explicit library_name; fall back to tags
    lib = (library_name or "").lower()
    tags_lower = [t.lower() for t in (tags or [])]
    if any(GGUF_PATTERN.search(t or "") for t in tags_lower):
        return "llama-cpp"
    if any("gguf" in t for t in tags_lower):
        return "llama-cpp"
    if "llama.cpp" in tags_lower or "gguf" in lib:
        return "llama-cpp"
    if "transformers" in tags_lower or lib in {"transformers", "pytorch", "tensorflow"}:
        return "transformers"
    # Heuristic: presence of safetensors/tokenizer/config implies transformers
    return "transformers"

def is_gguf_repo(files: List[FileEntry]) -> bool:
    return any(GGUF_PATTERN.search(f.path) for f in files)

# ---------- HF metadata ----------
def list_models_for_owner(owner: str, limit: int = 50, search: Optional[str] = None,
                          sort: str = "downloads", direction: int = -1) -> List[ModelSummary]:
    check_offline_mode()
    require_hf()
    
    # Configure API with mirror if specified
    api_kwargs = {}
    if _mirror_url:
        # Validate mirror connectivity first
        if not validate_mirror_connectivity(_mirror_url):
            bail(f"Mirror URL '{_mirror_url}' is not accessible", error_code="E_NET")
        api_kwargs['endpoint'] = _mirror_url
    
    api = HfApi(**api_kwargs)
    items = api.list_models(author=owner, search=search, limit=limit, sort=sort, direction=direction)
    results: List[ModelSummary] = []
    for m in items:
        results.append(ModelSummary(
            model_id=getattr(m, "modelId", ""),
            last_modified=getattr(m, "lastModified", None),
            likes=getattr(m, "likes", None),
            downloads=getattr(m, "downloads", None),
            library_name=getattr(m, "library_name", None) or getattr(m, "pipeline_tag", None),
            tags=list(getattr(m, "tags", []) or []),
        ))
    return results

def get_model_files(model_id: str, revision: Optional[str] = None) -> List[FileEntry]:
    check_offline_mode()
    require_hf()
    
    try:
        # Configure API with mirror if specified
        api_kwargs = {}
        if _mirror_url:
            api_kwargs['endpoint'] = _mirror_url
            
        info = model_info(repo_id=model_id, revision=revision, **api_kwargs)
    except HfHubHTTPError as e:
        bail(f"Failed to fetch model info for '{model_id}': {e}", error_code="E_NET")
    out: List[FileEntry] = []
    for s in getattr(info, "siblings", []) or []:
        out.append(FileEntry(path=getattr(s, "rfilename", "UNKNOWN"), size=getattr(s, "size", 0) or 0))
    return out

def print_model_table(models: Sequence[ModelSummary]) -> None:
    if _json_output:
        # Convert to JSON-serializable format
        models_data = []
        for m in models:
            model_dict = asdict(m)
            if model_dict['last_modified']:
                model_dict['last_modified'] = m.last_modified.isoformat()
            models_data.append(model_dict)
        result = OperationResult(
            success=True,
            message=f"Found {len(models)} models",
            data={"models": models_data}
        )
        output_result(result)
        return
        
    require_rich()
    tbl = Table(title="Hugging Face Models", box=box.SIMPLE_HEAVY)
    tbl.add_column("#", justify="right", style="bold")
    tbl.add_column("Model ID", style="cyan", overflow="fold")
    tbl.add_column("Downloads", justify="right")
    tbl.add_column("Likes", justify="right")
    tbl.add_column("Library")
    tbl.add_column("Last Modified")
    for i, m in enumerate(models, start=1):
        tbl.add_row(str(i), m.model_id, str(m.downloads or "-"), str(m.likes or "-"),
                    m.library_name or "-", human_dt(m.last_modified))
    console().print(tbl)

def print_files_table(files: Sequence[FileEntry], model_id: str = "") -> None:
    if _json_output:
        files_data = [asdict(f) for f in files]
        result = OperationResult(
            success=True,
            message=f"Model info for {model_id}" if model_id else "File information",
            data={
                "files": files_data,
                "total_size": sum_sizes(files),
                "file_count": len(files)
            }
        )
        output_result(result)
        return
        
    require_rich()
    tbl = Table(title="Repository Files", box=box.MINIMAL_HEAVY_HEAD)
    tbl.add_column("Path", style="green", overflow="fold")
    tbl.add_column("Size")
    for f in files:
        tbl.add_row(f.path, format_size(f.size))
    console().print(tbl)
    console().print(f"[bold]Total size:[/bold] {format_size(sum_sizes(files))}")

# ---------- Destination resolution & moves ----------
def resolve_install_root(model_id: str, library: str, files: List[FileEntry]) -> Path:
    """
    Decide TOP destination directory for a repo.
    """
    owner, repo = parse_owner_repo(model_id)

    # Special pin for distilbert to maintain your existing path
    if model_id == "distilbert-base-uncased" or repo == "distilbert-base-uncased":
        return DISTILBERT_PIN

    # Override by content
    if is_gguf_repo(files) or library == "llama-cpp":
        base = LLAMACPP_DIR / (owner if owner != "_" else repo) / (repo if owner != "_" else "")
        return base

    # Default: transformers repo
    base = TRANSFORMERS_DIR / (owner if owner != "_" else repo) / (repo if owner != "_" else "")
    return base

def safe_move_tree(src: Path, dst: Path) -> None:
    """
    Move all contents of src into dst, merging if needed; creates dst.
    """
    ensure_dir(dst)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if target.exists() and target.is_file():
                target.unlink()
            ensure_dir(target)
            safe_move_tree(item, target)
            # if now empty, remove
            try:
                item.rmdir()
            except OSError:
                pass
        else:
            if target.exists():
                # Don't clobber identical files; if sizes differ, overwrite with newer
                if item.stat().st_size == target.stat().st_size:
                    item.unlink()
                    continue
                target.unlink()
            shutil.move(str(item), str(target))

def copy_shared_configs(repo_root: Path, repo_name: str) -> None:
    """
    Copy a 'config.json' (if present) into models/configs/<repo_name>.json
    for quick lookup across engines.
    """
    cfg = repo_root / "config.json"
    if cfg.exists() and cfg.is_file():
        ensure_dir(CONFIGS_DIR)
        dst = CONFIGS_DIR / f"{repo_name}.json"
        shutil.copy2(cfg, dst)

# ---------- Registry ----------
def load_registry() -> Dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_registry(data: Dict[str, dict]) -> None:
    ensure_dir(MODELS_ROOT)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)

def update_registry(model_id: str, install_path: Path, files: List[FileEntry],
                    library: str, revision: Optional[str]) -> None:
    reg = load_registry()
    owner, repo = parse_owner_repo(model_id)
    key = f"{owner}/{repo}" if owner != "_" else repo
    reg[key] = {
        "model_id": model_id,
        "library": library,
        "revision": revision or "main",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "install_path": str(install_path.resolve()),
        "files": [{"path": f.path, "size": f.size} for f in files],
        "total_size": sum_sizes(files),
    }
    save_registry(reg)

# ---------- Download ----------
def download_snapshot(model_id: str, out_dir: Path, revision: Optional[str],
                      include: Optional[List[str]], exclude: Optional[List[str]],
                      resume: bool, max_workers: Optional[int]) -> Path:
    check_offline_mode()
    require_hf()
    ensure_dir(out_dir)
    
    # Configure download with mirror if specified
    download_kwargs = {
        "repo_id": model_id,
        "revision": revision,
        "local_dir": str(out_dir),
        "local_dir_use_symlinks": False,
        "allow_patterns": include,
        "ignore_patterns": exclude,
        "resume_download": resume,
        "max_workers": max_workers,
    }
    
    if _mirror_url:
        download_kwargs['endpoint'] = _mirror_url
    
    path = snapshot_download(**download_kwargs)
    return Path(path)

# ---------- Migrations (fix legacy layout you showed) ----------
def migrate_layout() -> None:
    """
    - Move llama-cpp GGUF into per-model directory
    - Remove .corrupt files
    - Keep distilbert in its pinned folder
    - Keep transformers/gpt2 under transformers/gpt2 (already good)
    - Ensure configs mirrored into models/configs/
    """
    console().print("[bold]Migrating existing layout...[/bold]")

    # 1) Fix llama-cpp root files like tinyllama-*.gguf.corrupt
    if LLAMACPP_DIR.exists():
        for item in LLAMACPP_DIR.glob("**/*"):
            if item.is_file() and GGUF_PATTERN.search(item.name):
                # Attempt to infer model subdir if sitting directly under llama-cpp
                rel = item.relative_to(LLAMACPP_DIR)
                if len(rel.parts) == 1:
                    # Heuristic for TinyLlama
                    repo = "TinyLlama-1.1B-Chat-v1.0"
                    owner = "TinyLlama"
                    target = LLAMACPP_DIR / owner / repo
                    ensure_dir(target)
                    if item.name.endswith(".corrupt"):
                        console().print(f"[yellow]Removing corrupt file:[/yellow] {item}")
                        item.unlink(missing_ok=True)
                    else:
                        dst = target / item.name
                        if dst.exists():
                            if item.stat().st_size == dst.stat().st_size:
                                item.unlink()
                            else:
                                dst.unlink()
                                shutil.move(str(item), str(dst))
                        else:
                            shutil.move(str(item), str(dst))

    # 2) Ensure transformer configs are copied
    # distilbert pin
    if DISTILBERT_PIN.exists():
        copy_shared_configs(DISTILBERT_PIN, "distilbert-base-uncased")
    # transformers subtree
    if TRANSFORMERS_DIR.exists():
        for repo_root in TRANSFORMERS_DIR.glob("*/*"):
            if repo_root.is_dir():
                repo_name = repo_root.name
                copy_shared_configs(repo_root, repo_name)

    console().print("[green]Migration complete.[/green]")

# ---------- Ensure helpers ----------
def _ensure_file(path: Path, url: str) -> None:
    """Download a file to path if missing or empty (simple bootstrap fetch).

    Uses urllib to avoid adding heavy deps. Caller ensures parent exists.
    """
    if path.exists() and path.stat().st_size > 0:
        console().print(f"[green]Model present:[/green] {path.name}")
        return
    try:
        import urllib.request
        path.parent.mkdir(parents=True, exist_ok=True)
        console().print(f"[cyan]Downloading:[/cyan] {url} -> {path}")
        urllib.request.urlretrieve(url, path)  # nosec - controlled URL configured by ops
        console().print(f"[green]Downloaded:[/green] {path}")
    except Exception as e:
        bail(f"Failed to download {url}: {e}", error_code="E_NET")

def ensure_tinyllama() -> None:
    """Ensure TinyLlama GGUF exists locally under models/llama-cpp.

    Downloads TinyLlama first (bootstrap convenience) without changing any runtime default.
    URL and filename can be overridden via env vars to allow rotation.
    """
    # Respect offline mode
    check_offline_mode()

    # Resolve target path inside llama-cpp models dir
    llama_dir = MODELS_ROOT / "llama-cpp"
    llama_dir.mkdir(parents=True, exist_ok=True)

    # Allow ops to override filename/URL
    filename = os.getenv("TINY_LLAMA_FILENAME", "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf")
    url = os.getenv(
        "TINY_LLAMA_URL",
        "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/"
        "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
    )
    target = llama_dir / filename

    # Simple size/magic check post-download
    _ensure_file(target, url)
    try:
        ok = False
        if target.exists() and target.stat().st_size > 50 * 1024 * 1024:
            with open(target, "rb") as f:
                magic = f.read(4)
            ok = magic == b"GGUF"
        if not ok:
            raise RuntimeError("download validation failed (magic/size)")
    except Exception as e:
        # Mark corrupt and surface error; leave file for inspection
        corrupt = target.with_suffix(target.suffix + ".corrupt")
        try:
            target.replace(corrupt)
        except Exception:
            pass
        bail(f"TinyLlama validation failed: {e}", error_code="E_VERIFY")
def ensure_distilbert() -> None:
    require_hf()
    if DISTILBERT_PIN.exists() and any(DISTILBERT_PIN.iterdir()):
        console().print(f"[green]DistilBERT present:[/green] {DISTILBERT_PIN}")
        return
    console().print("[cyan]Downloading distilbert-base-uncased...[/cyan]")
    download_snapshot(
        model_id="distilbert-base-uncased",
        out_dir=DISTILBERT_PIN,
        revision=None,
        include=None,
        exclude=None,
        resume=True,
        max_workers=None,
    )
    copy_shared_configs(DISTILBERT_PIN, "distilbert-base-uncased")
    update_registry("distilbert-base-uncased", DISTILBERT_PIN, get_model_files("distilbert-base-uncased"),
                    "transformers", None)
    console().print(f"[green]Done:[/green] {DISTILBERT_PIN}")

def ensure_spacy(model: str = "en_core_web_trf") -> None:
    try:
        import spacy  # noqa
    except Exception:
        console().print("[yellow]spaCy not installed; skipping.[/yellow]")
        return
    import subprocess
    try:
        import spacy as _sp  # type: ignore
        _sp.load(model)
        console().print(f"[green]spaCy model present:[/green] {model}")
    except OSError:
        console().print(f"[cyan]Downloading spaCy model:[/cyan] {model}")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", model])

def ensure_basic_classifier() -> None:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.feature_extraction.text import TfidfVectorizer
        import joblib  # type: ignore
    except Exception:
        console().print("[yellow]sklearn/joblib missing; skipping basic classifier.[/yellow]")
        return
    root = MODELS_ROOT / "basic_cls"
    clf_p = root / "classifier.joblib"
    vec_p = root / "vectorizer.joblib"
    if clf_p.exists() and vec_p.exists():
        console().print(f"[green]Basic classifier present:[/green] {root}")
        return
    ensure_dir(root)
    texts = ["hello", "hi", "goodbye", "bye", "thanks", "thank you"]
    labels = ["greet", "greet", "farewell", "farewell", "thanks", "thanks"]
    vect = TfidfVectorizer(max_features=1000).fit(texts)
    X = vect.transform(texts)
    clf = LogisticRegression(max_iter=1000).fit(X, labels)
    import joblib  # type: ignore
    joblib.dump(clf, clf_p)
    joblib.dump(vect, vec_p)
    console().print(f"[green]Created basic classifier:[/green] {root}")

# ---------- CLI Commands ----------
def cmd_list(args: argparse.Namespace) -> None:
    owner = args.owner
    if not owner:
        bail("Provide --owner", error_code="E_ARGS")
    
    try:
        models = list_models_for_owner(owner, limit=args.limit, search=args.search, sort=args.sort, direction=args.direction)
        if not models:
            bail(f"No models for '{owner}'.", error_code="E_NOT_FOUND")
        print_model_table(models)
    except Exception as e:
        bail(f"Failed to list models for '{owner}': {e}", error_code="E_NET")

def cmd_info(args: argparse.Namespace) -> None:
    try:
        files = get_model_files(args.model, revision=args.revision)
        if not _json_output:
            console().print(f"[bold]Model:[/bold] {args.model}")
        print_files_table(files, args.model)
    except Exception as e:
        bail(f"Failed to get model info for '{args.model}': {e}", error_code="E_NET")

def cmd_download(args: argparse.Namespace) -> None:
    try:
        # fetch metadata to decide layout before download
        files = get_model_files(args.model, revision=args.revision)
        total_size = sum_sizes(files)
        
        # Check storage quota if configured
        max_quota_gb = getattr(args, 'max_quota_gb', None)  # Could be set via config
        quota_ok, quota_msg = check_storage_quota(total_size, max_quota_gb=max_quota_gb)
        if not quota_ok:
            bail(quota_msg, error_code="E_QUOTA")
        
        # Check disk space
        models_path = MODELS_ROOT
        ensure_dir(models_path)
        total_disk, used_disk, free_disk = get_disk_usage(models_path)
        
        if total_size > free_disk:
            bail(f"Insufficient disk space: {format_size(total_size)} required, {format_size(free_disk)} available", 
                 error_code="E_DISK")
        
        # Run compatibility check if not in quiet mode
        if not _quiet_mode and not _json_output:
            try:
                # Create a temporary args object for compatibility check
                import types
                compat_args = types.SimpleNamespace()
                compat_args.model = args.model
                
                # Run compatibility check but don't exit on failure
                if psutil is not None:
                    cpu_features = detect_cpu_features()
                    gpu_info = detect_gpu_info()
                    ram_gb = psutil.virtual_memory().total / (1024**3)
                    
                    # Quick compatibility assessment
                    is_gguf = is_gguf_repo(files)
                    total_size_gb = total_size / (1024**3)
                    
                    warnings = []
                    if is_gguf:
                        min_ram = total_size_gb * 1.2
                        if min_ram > ram_gb:
                            warnings.append(f"Low RAM: {ram_gb:.1f}GB available, {min_ram:.1f}GB recommended")
                        if "x86_64" in cpu_features and "avx2" not in cpu_features:
                            warnings.append("AVX2 not detected - performance may be reduced")
                    else:
                        min_ram = total_size_gb * 2.0
                        if min_ram > ram_gb:
                            warnings.append(f"Low RAM: {ram_gb:.1f}GB available, {min_ram:.1f}GB recommended")
                        if total_size_gb > 2 and not gpu_info["available"]:
                            warnings.append("Large model without GPU - inference will be slow")
                    
                    if warnings:
                        console().print("[yellow]Compatibility warnings:[/yellow]")
                        for warning in warnings:
                            console().print(f"  • {warning}")
                        
                        # Suggest alternatives
                        suggestions = suggest_alternatives(args.model, warnings)
                        if suggestions:
                            console().print("\n[cyan]Suggestions:[/cyan]")
                            for suggestion in suggestions:
                                console().print(f"  • {suggestion}")
                        
                        if args.force_compat:
                            bail("Download blocked due to compatibility issues (use without --force-compat to override)", error_code="E_COMPAT")
                        elif not Confirm.ask("\nContinue with download?", default=True):
                            bail("Download cancelled by user", error_code="E_COMPAT")
                            
            except Exception:
                # Don't fail download if compatibility check fails
                pass
        
        # library guess
        # grab library_name/tags from list call (optional)
        lib_guess = args.library or "transformers"
        dest_root = resolve_install_root(args.model, lib_guess, files)
        ensure_dir(dest_root)
        
        # download directly into the resolved place
        if not _quiet_mode and not _json_output:
            console().print(f"[cyan]Installing into:[/cyan] {dest_root}")
            console().print(f"[cyan]Model size:[/cyan] {format_size(total_size)}")
            
        path = download_snapshot(
            model_id=args.model,
            out_dir=dest_root,
            revision=args.revision,
            include=args.include,
            exclude=args.exclude,
            resume=not args.no_resume,
            max_workers=args.max_workers,
        )
        
        # Shared config mirror
        _, repo = parse_owner_repo(args.model)
        copy_shared_configs(dest_root, repo)
        
        # purge obvious corrupt leftovers
        for bad in dest_root.rglob("*.corrupt"):
            if not _quiet_mode and not _json_output:
                console().print(f"[yellow]Removing corrupt piece:[/yellow] {bad}")
            bad.unlink(missing_ok=True)
            
        # registry
        library = "llama-cpp" if is_gguf_repo(files) else "transformers"
        update_registry(args.model, dest_root, files, library, args.revision)
        
        result = OperationResult(
            success=True,
            message=f"Successfully downloaded {args.model}",
            data={
                "model_id": args.model,
                "install_path": str(dest_root),
                "library": library,
                "total_size": sum_sizes(files),
                "file_count": len(files)
            }
        )
        output_result(result)
        
    except Exception as e:
        bail(f"Failed to download '{args.model}': {e}", error_code="E_NET")

def cmd_browse(args: argparse.Namespace) -> None:
    if _json_output:
        bail("Browse command is interactive and not supported in JSON mode. Use 'list' and 'download' commands instead.", error_code="E_ARGS")
        
    require_rich()
    owner = args.owner
    if not owner:
        bail("Provide --owner for browse.", error_code="E_ARGS")
        
    try:
        models = list_models_for_owner(owner, limit=args.limit)
        if not models:
            bail(f"No models for '{owner}'.", error_code="E_NOT_FOUND")
            
        print_model_table(models)
        sel = Prompt.ask("Select model number (or 'q')")
        if str(sel).lower().startswith("q"):
            return
            
        try:
            idx = int(sel) - 1
            assert 0 <= idx < len(models)
        except Exception:
            bail("Invalid selection.", error_code="E_ARGS")
            
        chosen = models[idx]
        files = get_model_files(chosen.model_id)
        print_files_table(files, chosen.model_id)
        lib = choose_library(chosen.tags, chosen.library_name)
        dest_root = resolve_install_root(chosen.model_id, lib, files)
        console().print(f"[bold]Will install into:[/bold] {dest_root}")
        
        if not Confirm.ask("Proceed?", default=True):
            console().print("[yellow]Cancelled.[/yellow]")
            return
            
        ensure_dir(dest_root)
        path = download_snapshot(
            model_id=chosen.model_id,
            out_dir=dest_root,
            revision=None,
            include=None,
            exclude=None,
            resume=True,
            max_workers=None,
        )
        
        _, repo = parse_owner_repo(chosen.model_id)
        copy_shared_configs(dest_root, repo)
        for bad in dest_root.rglob("*.corrupt"):
            bad.unlink(missing_ok=True)
            
        update_registry(chosen.model_id, dest_root, files, lib, None)
        console().print(f"[green]Downloaded to:[/green] {path}")
        
    except Exception as e:
        bail(f"Browse operation failed: {e}", error_code="E_NET")

def cmd_migrate(args: argparse.Namespace) -> None:
    try:
        migrate_layout()
        result = OperationResult(
            success=True,
            message="Migration completed successfully",
            data={"operation": "migrate"}
        )
        output_result(result)
    except Exception as e:
        bail(f"Migration failed: {e}", error_code="E_DISK")

def cmd_ensure(args: argparse.Namespace) -> None:
    try:
        operations = []
        if getattr(args, "tinyllama", False):
            ensure_tinyllama()
            operations.append("tinyllama")
        if args.distilbert: 
            ensure_distilbert()
            operations.append("distilbert")
        if args.spacy: 
            ensure_spacy()
            operations.append("spacy")
        if args.basic_cls: 
            ensure_basic_classifier()
            operations.append("basic_classifier")
            
        if not operations:
            bail("Nothing to ensure. Use --tinyllama --distilbert --spacy --basic-cls", error_code="E_ARGS")
            
        result = OperationResult(
            success=True,
            message=f"Ensured models: {', '.join(operations)}",
            data={"operations": operations}
        )
        output_result(result)
        
    except Exception as e:
        bail(f"Ensure operation failed: {e}", error_code="E_NET")

def get_disk_usage(path: Path) -> tuple[int, int, int]:
    """Get disk usage statistics for a path (total, used, free in bytes)"""
    if psutil:
        usage = psutil.disk_usage(str(path))
        return usage.total, usage.used, usage.free
    else:
        # Fallback using shutil
        usage = shutil.disk_usage(str(path))
        return usage.total, usage.used, usage.free

def check_disk_space_low(path: Path, threshold_percent: float = 90.0) -> bool:
    """Check if disk space is low (above threshold percentage)"""
    try:
        total, used, free = get_disk_usage(path)
        used_percent = (used / total) * 100
        return used_percent > threshold_percent
    except Exception:
        return False

def get_user_storage_usage(user_id: str = "default") -> int:
    """Get total storage usage for a user in bytes"""
    registry = load_registry()
    total_usage = 0
    
    for key, entry in registry.items():
        # For now, all models belong to default user
        # In future, could track per-user ownership
        total_usage += entry.get("total_size", 0)
    
    return total_usage

def check_storage_quota(model_size: int, user_id: str = "default", max_quota_gb: Optional[float] = None) -> tuple[bool, str]:
    """Check if adding a model would exceed storage quota"""
    if max_quota_gb is None:
        return True, ""  # No quota configured
    
    current_usage = get_user_storage_usage(user_id)
    max_quota_bytes = int(max_quota_gb * 1024 * 1024 * 1024)
    
    if current_usage + model_size > max_quota_bytes:
        current_gb = current_usage / (1024**3)
        model_gb = model_size / (1024**3)
        return False, f"Storage quota exceeded: {current_gb:.1f}GB + {model_gb:.1f}GB > {max_quota_gb:.1f}GB limit"
    
    return True, ""

def suggest_alternatives(model_id: str, compatibility_issues: List[str]) -> List[str]:
    """Suggest alternative models based on compatibility issues"""
    suggestions = []
    
    # Parse model owner and name
    owner, repo = parse_owner_repo(model_id)
    
    # Common alternative suggestions based on issues
    if any("RAM" in issue for issue in compatibility_issues):
        suggestions.append("Consider a smaller quantized version (Q4_K_M or Q8_0)")
        if "llama" in model_id.lower():
            suggestions.append("Try TinyLlama/TinyLlama-1.1B-Chat-v1.0 for lower memory usage")
        suggestions.append("Use GGUF format for more efficient memory usage")
    
    if any("GPU" in issue for issue in compatibility_issues):
        suggestions.append("Consider CPU-optimized GGUF models")
        suggestions.append("Look for quantized versions that run well on CPU")
    
    if any("AVX" in issue for issue in compatibility_issues):
        suggestions.append("Look for models optimized for older CPUs")
        suggestions.append("Consider using transformers library instead of llama.cpp")
    
    if any("disk" in issue.lower() for issue in compatibility_issues):
        suggestions.append("Free up space with 'gc' command")
        suggestions.append("Consider smaller model variants")
    
    return suggestions

def cmd_gc(args: argparse.Namespace) -> None:
    """Garbage collect unused models based on LRU and pinning status"""
    try:
        registry = load_registry()
        if not registry:
            result = OperationResult(
                success=True,
                message="No models to garbage collect",
                data={"removed_models": [], "freed_space": 0}
            )
            output_result(result)
            return
        
        # Check disk space status
        models_path = MODELS_ROOT
        ensure_dir(models_path)
        total, used, free = get_disk_usage(models_path)
        used_percent = (used / total) * 100
        disk_low = check_disk_space_low(models_path, 85.0)  # 85% threshold
        
        if not _quiet_mode and not _json_output:
            console().print(f"[cyan]Disk usage:[/cyan] {format_size(used)}/{format_size(total)} ({used_percent:.1f}%)")
            if disk_low:
                console().print("[yellow]Warning: Disk space is low[/yellow]")
            
        # Sort by last_accessed (LRU), skip pinned models
        candidates = []
        for key, entry in registry.items():
            if entry.get("pinned", False):
                continue  # Skip pinned models
                
            install_path = Path(entry.get("install_path", ""))
            if not install_path.exists():
                candidates.append((key, entry, 0))  # Missing models get priority for cleanup
            else:
                # Use last_accessed or installed_at as fallback
                last_access = entry.get("last_accessed", entry.get("installed_at"))
                candidates.append((key, entry, last_access))
        
        # Sort by access time (oldest first)
        candidates.sort(key=lambda x: x[2] or "")
        
        removed_models = []
        freed_space = 0
        target_space = args.target_gb * 1024 * 1024 * 1024 if args.target_gb else None
        
        # If disk is low and no target specified, aim to free 20% of total space
        if disk_low and target_space is None:
            target_space = int(total * 0.2)
        
        # Check quota enforcement
        if args.quota_gb:
            current_usage = get_user_storage_usage()
            quota_bytes = int(args.quota_gb * 1024 * 1024 * 1024)
            if current_usage > quota_bytes:
                excess = current_usage - quota_bytes
                if target_space is None or excess > target_space:
                    target_space = excess
                    if not _quiet_mode and not _json_output:
                        console().print(f"[yellow]Quota exceeded:[/yellow] {format_size(current_usage)} > {format_size(quota_bytes)}")
                        console().print(f"[yellow]Need to free:[/yellow] {format_size(excess)}")
        
        for key, entry, _ in candidates:
            if args.dry_run:
                removed_models.append({
                    "model_id": entry.get("model_id", key),
                    "size": entry.get("total_size", 0),
                    "path": entry.get("install_path", "")
                })
                freed_space += entry.get("total_size", 0)
                continue
                
            # Actually remove the model
            install_path = Path(entry.get("install_path", ""))
            if install_path.exists():
                try:
                    shutil.rmtree(install_path)
                    model_size = entry.get("total_size", 0)
                    freed_space += model_size
                    removed_models.append({
                        "model_id": entry.get("model_id", key),
                        "size": model_size,
                        "path": str(install_path)
                    })
                    
                    # Remove from registry
                    del registry[key]
                    
                    if not _quiet_mode and not _json_output:
                        console().print(f"[yellow]Removed:[/yellow] {entry.get('model_id', key)} ({format_size(model_size)})")
                        
                    # Check if we've freed enough space
                    if target_space and freed_space >= target_space:
                        break
                        
                except Exception as e:
                    if not _quiet_mode and not _json_output:
                        console().print(f"[red]Failed to remove {key}:[/red] {e}")
            else:
                # Remove from registry if path doesn't exist
                del registry[key]
                removed_models.append({
                    "model_id": entry.get("model_id", key),
                    "size": 0,
                    "path": str(install_path),
                    "note": "Path not found"
                })
        
        # Save updated registry
        if not args.dry_run and removed_models:
            save_registry(registry)
            
        result = OperationResult(
            success=True,
            message=f"Garbage collection {'(dry run) ' if args.dry_run else ''}completed. Freed {format_size(freed_space)}",
            data={
                "removed_models": removed_models,
                "freed_space": freed_space,
                "dry_run": args.dry_run
            }
        )
        output_result(result)
        
    except Exception as e:
        bail(f"Garbage collection failed: {e}", error_code="E_DISK")

def cmd_pin(args: argparse.Namespace) -> None:
    """Pin or unpin models to protect from garbage collection"""
    try:
        registry = load_registry()
        model_key = None
        
        # Find the model in registry
        for key, entry in registry.items():
            if entry.get("model_id") == args.model or key == args.model:
                model_key = key
                break
                
        if not model_key:
            bail(f"Model '{args.model}' not found in registry", error_code="E_NOT_FOUND")
            
        # Update pin status
        registry[model_key]["pinned"] = not args.unpin
        save_registry(registry)
        
        action = "unpinned" if args.unpin else "pinned"
        result = OperationResult(
            success=True,
            message=f"Model '{args.model}' {action}",
            data={
                "model_id": args.model,
                "pinned": not args.unpin,
                "action": action
            }
        )
        output_result(result)
        
    except Exception as e:
        bail(f"Pin operation failed: {e}", error_code="E_DISK")

def detect_cpu_features() -> List[str]:
    """Detect available CPU features"""
    import platform
    features = []
    
    # Basic architecture detection
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        features.append("x86_64")
        
        # Try to detect AVX support
        try:
            import subprocess
            # Check for AVX support on Linux/macOS
            if platform.system().lower() in ['linux', 'darwin']:
                result = subprocess.run(['grep', '-m1', 'flags', '/proc/cpuinfo'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    flags = result.stdout.lower()
                    if 'avx2' in flags:
                        features.append("avx2")
                    elif 'avx' in flags:
                        features.append("avx")
                    if 'sse4_2' in flags:
                        features.append("sse4_2")
                    if 'sse4_1' in flags:
                        features.append("sse4_1")
        except Exception:
            # Fallback: assume basic features for x86_64
            features.extend(["sse4_1", "sse4_2"])
            
    elif machine in ['arm64', 'aarch64']:
        features.append("arm64")
        features.append("neon")  # Most ARM64 systems have NEON
        
    return features

def detect_gpu_info() -> dict:
    """Detect GPU availability and VRAM"""
    gpu_info = {
        "available": False,
        "cuda_available": False,
        "vram_gb": 0,
        "gpu_count": 0,
        "gpu_names": []
    }
    
    try:
        import subprocess
        # Check NVIDIA GPUs
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', 
                               '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            gpu_info["available"] = True
            gpu_info["cuda_available"] = True
            lines = result.stdout.strip().split('\n')
            total_vram = 0
            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        gpu_name = parts[0].strip()
                        vram_mb = int(parts[1].strip())
                        gpu_info["gpu_names"].append(gpu_name)
                        total_vram += vram_mb
                        gpu_info["gpu_count"] += 1
            gpu_info["vram_gb"] = total_vram / 1024
    except Exception:
        pass
    
    # Check for other GPU types (AMD, Intel) if NVIDIA not found
    if not gpu_info["available"]:
        try:
            import subprocess
            # Try lspci for other GPUs
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout.lower()
                if any(gpu in output for gpu in ['vga', 'display', 'graphics']):
                    gpu_info["available"] = True
        except Exception:
            pass
    
    return gpu_info

def cmd_compatibility(args: argparse.Namespace) -> None:
    """Check system compatibility for a model"""
    try:
        import platform
        
        if psutil is None:
            bail("psutil is required for compatibility checks. pip install psutil", error_code="E_ARGS")
        
        # Get detailed system info
        cpu_features = detect_cpu_features()
        gpu_info = detect_gpu_info()
        
        # Get memory info
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        # Get disk info
        models_path = MODELS_ROOT
        ensure_dir(models_path)
        total_disk, used_disk, free_disk = get_disk_usage(models_path)
        disk_gb = total_disk / (1024**3)
        free_disk_gb = free_disk / (1024**3)
        
        # Get model info if specified
        model_requirements = None
        if args.model:
            try:
                files = get_model_files(args.model)
                total_size_gb = sum_sizes(files) / (1024**3)
                
                # Estimate requirements based on model size and type
                is_gguf = is_gguf_repo(files)
                
                # More sophisticated requirement estimation
                if is_gguf:
                    # GGUF models typically run on CPU with some GPU acceleration
                    model_requirements = {
                        "min_ram_gb": total_size_gb * 1.2,  # GGUF is more memory efficient
                        "min_vram_gb": 0,  # Optional for GGUF
                        "min_disk_gb": total_size_gb * 1.1,  # Small overhead
                        "gpu_required": False,
                        "cpu_features_required": ["x86_64"] if "x86_64" in cpu_features else [],
                        "recommended_features": ["avx2", "avx"] if "x86_64" in cpu_features else ["neon"]
                    }
                else:
                    # Transformers models typically need more resources
                    model_requirements = {
                        "min_ram_gb": total_size_gb * 2.0,  # Transformers need more memory
                        "min_vram_gb": total_size_gb * 1.5 if total_size_gb > 1 else 0,
                        "min_disk_gb": total_size_gb * 1.2,
                        "gpu_required": total_size_gb > 2,  # Large models benefit from GPU
                        "cpu_features_required": [],
                        "recommended_features": ["avx2"] if "x86_64" in cpu_features else []
                    }
                    
            except Exception as e:
                if not _quiet_mode and not _json_output:
                    console().print(f"[yellow]Warning: Could not get model requirements: {e}[/yellow]")
        
        # Check compatibility
        warnings = []
        recommendations = []
        compatible = True
        
        if model_requirements:
            # Check RAM
            if model_requirements["min_ram_gb"] > ram_gb:
                warnings.append(f"Insufficient RAM: {ram_gb:.1f}GB available, {model_requirements['min_ram_gb']:.1f}GB required")
                compatible = False
            
            # Check VRAM if GPU required
            if model_requirements["gpu_required"] and not gpu_info["available"]:
                warnings.append("GPU required but not available")
                compatible = False
            elif model_requirements["min_vram_gb"] > 0 and gpu_info["vram_gb"] < model_requirements["min_vram_gb"]:
                warnings.append(f"Insufficient VRAM: {gpu_info['vram_gb']:.1f}GB available, {model_requirements['min_vram_gb']:.1f}GB required")
                compatible = False
            
            # Check disk space
            if model_requirements["min_disk_gb"] > free_disk_gb:
                warnings.append(f"Insufficient disk space: {free_disk_gb:.1f}GB available, {model_requirements['min_disk_gb']:.1f}GB required")
                compatible = False
            
            # Check required CPU features
            for feature in model_requirements["cpu_features_required"]:
                if feature not in cpu_features:
                    warnings.append(f"Missing required CPU feature: {feature}")
                    compatible = False
            
            # Check recommended features
            for feature in model_requirements["recommended_features"]:
                if feature not in cpu_features:
                    recommendations.append(f"Recommended CPU feature missing: {feature} (performance may be reduced)")
        
        # General system warnings
        if ram_gb < 8:
            recommendations.append("System has less than 8GB RAM - consider upgrading for better performance")
        
        if not gpu_info["available"] and args.model:
            recommendations.append("No GPU detected - CPU-only inference will be slower")
        
        compatibility_info = CompatibilityInfo(
            cpu_features=cpu_features,
            gpu_required=model_requirements["gpu_required"] if model_requirements else False,
            min_ram_gb=model_requirements["min_ram_gb"] if model_requirements else 0,
            min_vram_gb=model_requirements["min_vram_gb"] if model_requirements else 0,
            compatible=compatible,
            warnings=warnings + recommendations
        )
        
        result = OperationResult(
            success=True,
            message=f"Compatibility check {'passed' if compatible else 'failed'}",
            data={
                "model_id": args.model,
                "system": {
                    "cpu_features": cpu_features,
                    "gpu_info": gpu_info,
                    "ram_gb": ram_gb,
                    "disk_gb": disk_gb,
                    "free_disk_gb": free_disk_gb
                },
                "model_requirements": model_requirements,
                "compatibility": asdict(compatibility_info),
                "warnings": warnings,
                "recommendations": recommendations
            }
        )
        output_result(result)
        
        if not _json_output:
            if warnings:
                for warning in warnings:
                    console().print(f"[red]Warning:[/red] {warning}")
            if recommendations:
                for rec in recommendations:
                    console().print(f"[yellow]Recommendation:[/yellow] {rec}")
            
            # Show system summary
            console().print(f"\n[bold]System Summary:[/bold]")
            console().print(f"CPU: {platform.machine()} with features: {', '.join(cpu_features)}")
            console().print(f"RAM: {ram_gb:.1f}GB")
            console().print(f"Disk: {free_disk_gb:.1f}GB free of {disk_gb:.1f}GB total")
            if gpu_info["available"]:
                console().print(f"GPU: {gpu_info['gpu_count']} GPU(s) with {gpu_info['vram_gb']:.1f}GB VRAM")
                for gpu_name in gpu_info["gpu_names"]:
                    console().print(f"  - {gpu_name}")
            else:
                console().print("GPU: Not available")
                
    except Exception as e:
        bail(f"Compatibility check failed: {e}", error_code="E_COMPAT")

def cmd_license(args: argparse.Namespace) -> None:
    """Handle license acceptance workflow"""
    try:
        if args.accept:
            # Accept license for a model
            registry = load_registry()
            model_key = None
            
            # Find the model in registry
            for key, entry in registry.items():
                if entry.get("model_id") == args.model or key == args.model:
                    model_key = key
                    break
                    
            if not model_key:
                bail(f"Model '{args.model}' not found in registry", error_code="E_NOT_FOUND")
                
            # Record license acceptance
            registry[model_key]["license_accepted"] = {
                "user_id": args.user_id or "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "license_type": args.license_type or "unknown"
            }
            save_registry(registry)
            
            result = OperationResult(
                success=True,
                message=f"License accepted for '{args.model}'",
                data={
                    "model_id": args.model,
                    "user_id": args.user_id,
                    "timestamp": registry[model_key]["license_accepted"]["timestamp"]
                }
            )
            output_result(result)
            
        elif args.show:
            # Show license info for a model
            try:
                # Try to get license info from HuggingFace
                check_offline_mode()
                require_hf()
                
                api_kwargs = {}
                if _mirror_url:
                    api_kwargs['endpoint'] = _mirror_url
                    
                info = model_info(repo_id=args.model, **api_kwargs)
                license_type = getattr(info, 'license', None)
                
                # Check if already accepted
                registry = load_registry()
                accepted_info = None
                for key, entry in registry.items():
                    if entry.get("model_id") == args.model or key == args.model:
                        accepted_info = entry.get("license_accepted")
                        break
                
                result = OperationResult(
                    success=True,
                    message=f"License information for '{args.model}'",
                    data={
                        "model_id": args.model,
                        "license_type": license_type,
                        "requires_acceptance": license_type not in [None, "apache-2.0", "mit", "bsd"],
                        "accepted": accepted_info is not None,
                        "acceptance_info": accepted_info
                    }
                )
                output_result(result)
                
            except Exception as e:
                bail(f"Could not retrieve license info: {e}", error_code="E_NET")
        else:
            bail("Use --accept or --show with license command", error_code="E_ARGS")
            
    except Exception as e:
        bail(f"License operation failed: {e}", error_code="E_LICENSE")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="model_manager",
        description="Browse/Download HF models and normalize local layout under ./models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
          Examples:
            model_manager migrate
            model_manager list --owner TinyLlama
            model_manager info --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
            model_manager download --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --dest ./models
            model_manager browse --owner TinyLlama --dest ./models/llama-cpp
            model_manager ensure --distilbert --spacy --basic-cls
            
          JSON Output:
            model_manager --json list --owner TinyLlama
            model_manager --json info --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
            
          Quiet Mode:
            model_manager --quiet download --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
            
          Offline Mode:
            model_manager --offline gc --dry-run
            model_manager --offline compatibility
            
          Mirror Usage:
            model_manager --mirror https://hf-mirror.com list --owner TinyLlama
            model_manager --mirror https://hf-mirror.com download --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
        """),
    )
    
    # Global flags
    p.add_argument("--json", action="store_true", help="Output results in JSON format for machine processing")
    p.add_argument("--quiet", "-q", action="store_true", help="Suppress non-essential output (useful for automation)")
    p.add_argument("--offline", action="store_true", help="Operate in offline mode (no network access)")
    p.add_argument("--mirror", type=str, help="Use custom mirror URL instead of HuggingFace Hub")
    
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("migrate", help="Normalize/migrate current ./models layout")
    sp.set_defaults(func=cmd_migrate)

    sp = sub.add_parser("list", help="List models for an owner/org")
    sp.add_argument("--owner", required=True)
    sp.add_argument("--limit", type=int, default=50)
    sp.add_argument("--search", type=str, default=None)
    sp.add_argument("--sort", type=str, default="downloads", choices=["downloads", "likes", "modified"])
    sp.add_argument("--direction", type=int, default=-1)
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("info", help="Show model metadata & file sizes")
    sp.add_argument("--model", required=True)
    sp.add_argument("--revision", type=str, default=None)
    sp.set_defaults(func=cmd_info)

    sp = sub.add_parser("download", help="Download & install a model into correct folder")
    sp.add_argument("--model", required=True)
    sp.add_argument("--revision", type=str, default=None)
    sp.add_argument("--dest", type=Path, default=MODELS_ROOT)  # kept for symmetry; we always resolve within this root
    sp.add_argument("--include", action="append")
    sp.add_argument("--exclude", action="append")
    sp.add_argument("--max-workers", type=int, default=None)
    sp.add_argument("--no-resume", action="store_true")
    sp.add_argument("--library", type=str, default=None, help="Override library routing (llama-cpp|transformers)")
    sp.add_argument("--max-quota-gb", type=float, default=None, help="Maximum storage quota in GB")
    sp.add_argument("--force-compat", action="store_true", help="Block download if compatibility issues detected")
    sp.set_defaults(func=cmd_download)

    sp = sub.add_parser("browse", help="Interactive picker for an owner; installs to proper folder")
    sp.add_argument("--owner", required=True)
    sp.add_argument("--limit", type=int, default=50)
    sp.add_argument("--dest", type=Path, default=MODELS_ROOT)
    sp.set_defaults(func=cmd_browse)

    sp = sub.add_parser("ensure", help="Ensure baseline local models")
    sp.add_argument("--tinyllama", action="store_true", help="Ensure TinyLlama GGUF is present under models/llama-cpp")
    sp.add_argument("--distilbert", action="store_true")
    sp.add_argument("--spacy", action="store_true")
    sp.add_argument("--basic-cls", action="store_true")
    sp.set_defaults(func=cmd_ensure)

    sp = sub.add_parser("gc", help="Garbage collect unused models (LRU-based)")
    sp.add_argument("--dry-run", action="store_true", help="Show what would be removed without actually removing")
    sp.add_argument("--target-gb", type=float, help="Target amount of space to free in GB")
    sp.add_argument("--quota-gb", type=float, help="Enforce storage quota in GB")
    sp.set_defaults(func=cmd_gc)

    sp = sub.add_parser("pin", help="Pin/unpin models to protect from garbage collection")
    sp.add_argument("--model", required=True, help="Model ID to pin/unpin")
    sp.add_argument("--unpin", action="store_true", help="Unpin the model instead of pinning")
    sp.set_defaults(func=cmd_pin)

    sp = sub.add_parser("compatibility", help="Check system compatibility for models")
    sp.add_argument("--model", help="Model ID to check compatibility for")
    sp.set_defaults(func=cmd_compatibility)

    sp = sub.add_parser("license", help="Handle license acceptance workflow")
    sp.add_argument("--model", required=True, help="Model ID")
    sp.add_argument("--accept", action="store_true", help="Accept the license for the model")
    sp.add_argument("--show", action="store_true", help="Show license information")
    sp.add_argument("--user-id", help="User ID accepting the license")
    sp.add_argument("--license-type", help="License type being accepted")
    sp.set_defaults(func=cmd_license)

    return p

def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Set global output mode based on flags
    set_output_mode(json_output=args.json, quiet=args.quiet)
    set_network_mode(offline=args.offline, mirror_url=args.mirror)
    
    # Validate mirror connectivity if specified
    if args.mirror and not args.offline:
        if not validate_mirror_connectivity(args.mirror):
            bail(f"Mirror URL '{args.mirror}' is not accessible. Use --offline to skip connectivity check.", error_code="E_NET")
        elif not _quiet_mode and not _json_output:
            console().print(f"[green]Using mirror:[/green] {args.mirror}")
    
    # Show offline mode warning
    if args.offline and not _quiet_mode and not _json_output:
        console().print("[yellow]Running in offline mode - network operations will fail[/yellow]")
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        if _json_output:
            result = OperationResult(
                success=False,
                message="Operation interrupted by user",
                error_code="E_INTERRUPTED"
            )
            output_result(result)
        else:
            console().print("\n[red]Interrupted.[/red]")
        sys.exit(130)

if __name__ == "__main__":
    main()
