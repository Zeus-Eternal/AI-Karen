# Kari Model Manager v2
> Hugging Face browser, downloader, and filesystem normalizer for Kari.

## TL;DR
- Browse orgs/users on Hugging Face, inspect files/sizes, and **download with resume**.
- Install artifacts into a **deterministic layout** under `./models/` (GGUF vs Transformers).
- Maintain a living registry at `models/model_registry.json`.
- Migrate legacy trees idempotently; optionally **pin** models and **garbage-collect** by LRU.
- JSON output for automation, quiet mode for scripts, offline/mirror support for air-gapped use.

---

## Installation

```bash
pip install huggingface_hub==0.25.2 rich==13.7.1 humanfriendly==10.0 psutil
# Optional helpers:
pip install scikit-learn==1.4.2 joblib==1.4.2
pip install spacy==3.7.4 && python -m spacy download en_core_web_trf
````

---

## Deterministic Folder Layout

```
models/
├─ basic_cls/                       # sklearn quick model (ensure)
│  ├─ classifier.joblib
│  └─ vectorizer.joblib
├─ configs/                         # mirrored configs for quick discovery
│  └─ <repo>.json                   # copied from <install_path>/config.json
├─ distilbert-base-uncased/         # special pin for legacy compatibility
│  └─ <HF snapshot>
├─ llama-cpp/
│  └─ <owner>/<repo>/               # GGUF repos
│     └─ *.gguf
├─ transformers/
│  └─ <owner-or-plain>/<repo>/      # Transformers repos
│     ├─ model.safetensors | *.bin
│     ├─ tokenizer.json | vocab.json
│     └─ config.json
└─ model_registry.json              # single source of truth (SSOT)
```

**Routing rules**

* If any `*.gguf` -> `models/llama-cpp/<owner>/<repo>/`
* Else → `models/transformers/<owner-or-plain>/<repo>/`
* **Special case:** `distilbert-base-uncased` goes to `models/distilbert-base-uncased/`
* If `config.json` exists, it’s mirrored to `models/configs/<repo>.json`

---

## Registry (`models/model_registry.json`)

Each install/update writes a record:

```json
{
  "<owner>/<repo>": {
    "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "library": "llama-cpp",
    "revision": "main",
    "installed_at": "2025-09-01T12:34:56Z",
    "install_path": "/abs/path/models/llama-cpp/TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "files": [{ "path": "tinyllama-...Q4_K_M.gguf", "size": 123456789 }],
    "total_size": 123456789
    // Optional extras the tool may add over time:
    // "pinned": true, "license_accepted": {...}, "last_accessed": "...",
  }
}
```

> **Note:** This tool intentionally uses `model_registry.json` (separate from any legacy `llm_registry.json` you may already have).

---

## CLI Basics

Global flags:

* `--json` : machine-readable outputs
* `--quiet` / `-q` : suppress non-essential logs
* `--offline` : forbid network (operations needing network will error)
* `--mirror URL` : use HF mirror (connectivity is pre-checked)

### List Models

```bash
python model_manager.py list --owner TinyLlama
# Filters
python model_manager.py list --owner TinyLlama --search chat --sort downloads --direction -1
# JSON for automation
python model_manager.py --json list --owner TinyLlama
```

### Inspect Files & Size

```bash
python model_manager.py info --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
python model_manager.py --json info --model distilbert-base-uncased
```

### Download & Install (with resume, filters)

```bash
python model_manager.py download --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
# Include/exclude subsets
python model_manager.py download --model org/repo --include "*.gguf" --exclude "*.safetensors"
# Override routing if you know better
python model_manager.py download --model org/repo --library llama-cpp
# Enforce quota / compat guard
python model_manager.py download --model org/repo --max-quota-gb 40 --force-compat
```

**What happens**

* Resolves destination by content (GGUF vs Transformers) or `--library`.
* Checks disk/quota; shows size; downloads with `snapshot_download` (resumable).
* Mirrors `config.json` into `models/configs/`.
* Deletes `*.corrupt` leftovers.
* Updates `models/model_registry.json`.

### Interactive Browse

```bash
python model_manager.py browse --owner TinyLlama
```

Rich table → select a model → view files/sizes → confirm download.

> Not available with `--json`.

### Ensure Baseline Models

```bash
python model_manager.py ensure --distilbert --spacy --basic-cls
```

* DistilBERT (HF snapshot) → pinned path
* spaCy model `en_core_web_trf` (if spaCy present)
* Minimal sklearn classifier

### Garbage Collection (LRU) & Pinning

```bash
# Dry run, see what would be removed
python model_manager.py gc --dry-run --target-gb 20

# Enforce quota (removes oldest unpinned until under quota)
python model_manager.py gc --quota-gb 60

# Protect a model
python model_manager.py pin --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
# Or unpin it
python model_manager.py pin --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --unpin
```

### Compatibility Check (RAM/VRAM/CPU/GPU heuristics)

```bash
python model_manager.py compatibility --model TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

* Detects CPU features (x86\_64 AVX/AVX2/ARM NEON), GPUs/VRAM (via `nvidia-smi` if present), RAM, free disk.
* Estimates requirements from model size & format; prints warnings/recommendations.
* Use `--force-compat` on `download` to block on warnings.

### License Workflow

```bash
# Show license information (and acceptance status)
python model_manager.py license --model org/repo --show

# Record explicit acceptance
python model_manager.py license --model org/repo --accept --user-id admin@kari --license-type other
```

### Migration (idempotent)

```bash
python model_manager.py migrate
```

* Moves GGUF files into `<owner>/<repo>` subdirs.
* Removes `*.corrupt`.
* Mirrors configs into `models/configs/`.
* Safe to re-run; only fixes drift.

---

## Offline & Mirror Modes

* `--offline` forbids network (safe for GC/compat/migrate/local reads).
* `--mirror URL` points to a private HF mirror; connectivity is validated at startup.

> For air-gapped: pre-seed your HF cache or host a mirror; use `--offline` to avoid accidental calls.

---

## Error Codes (Structured)

* `E_NET` (network/mirror issues), `E_DISK` (space/I/O), `E_PERM`, `E_LICENSE`,
  `E_VERIFY` (integrity), `E_SCHEMA`, `E_COMPAT` (compatibility),
  `E_QUOTA`, `E_ARGS`, `E_NOT_FOUND`.

With `--json`, errors are emitted as:

```json
{
  "success": false,
  "message": "Insufficient disk space: ...",
  "error_code": "E_DISK",
  "data": null
}
```

---

## Programmatic Use (Import as a Module)

You can import and call the core helpers directly:

```python
from model_manager import (
    list_models_for_owner, get_model_files, resolve_install_root,
    download_snapshot, update_registry, load_registry
)

models = list_models_for_owner("TinyLlama", limit=10)
files = get_model_files("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
dest  = resolve_install_root("TinyLlama/TinyLlama-1.1B-Chat-v1.0", "llama-cpp", files)
path  = download_snapshot("TinyLlama/TinyLlama-1.1B-Chat-v1.0", dest, revision=None,
                          include=None, exclude=None, resume=True, max_workers=None)
# Mirror config, then register
from model_manager import copy_shared_configs, parse_owner_repo, is_gguf_repo
_, repo = parse_owner_repo("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
copy_shared_configs(dest, repo)
update_registry("TinyLlama/TinyLlama-1.1B-Chat-v1.0", dest, files,
                "llama-cpp" if is_gguf_repo(files) else "transformers", None)
```

> For machine-readable CLI outputs, prefer `--json`.

---

## Security & Integrity

* All registry writes are **atomic** (`.tmp` then replace).
* Quota & disk checks prevent partial installs.
* Optional license acceptance is recorded in registry (`license_accepted` block).
* No credentials are stored; HF auth (if needed) comes from your environment.

---

## Observability & Logging

* Human mode: rich tables + clear messages.
* Automation mode: `--json` everywhere.
* You can wrap the CLI in your own Prometheus/OTel runner to time:

  * resolve → download → verify → register → mirror-config phases.

---

## Troubleshooting

* **Mirror fails** → verify URL, TLS, and that your mirror hosts the repo.
* **Disk full** → run `gc --dry-run` then `gc` or raise quota, or use include globs.
* **No GPU** → prefer GGUF/quantized variants; check `compatibility`.
* **Offline** → ensure cache/mirror present; otherwise operations requiring network will emit `E_NET`.
* **Permission denied** → run with sufficient rights for `models/`.

---

## Examples

```bash
# Fast path: install a TinyLlama GGUF and be done
python model_manager.py download --model TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Air-gapped dry-run GC to plan cleanup
python model_manager.py --offline gc --dry-run

# Script-friendly: list → choose the top model → dump JSON to a file
python model_manager.py --json list --owner TinyLlama > tinyllama_models.json
```

---

## Why prompt-first (how the agent uses this)
The verbs are your **intents** (`list/info/download/browse/migrate/ensure/gc/pin/compatibility/license`). Agents can chain them deterministically, and the `--json` surface becomes the contract for orchestration and the web UI.

## Data science rationale
Deterministic layout + registry enables reproducibility, storage planning (via `total_size`), and compatibility heuristics at install time (RAM/VRAM/CPU checks derived from artifact sizes and formats).

## Test strategy
- Unit: route resolution (GGUF vs Transformers), registry writes, quota checks, JSON output shape.
- Integration: tiny HF model download, resume path, config mirroring, idempotent `migrate`.
- Failure injection: disk-full, offline/mirror timeout, corrupt file cleanup.

## Security checks
Atomic writes, explicit error taxonomy, optional license acceptance recording, and no secret persistence. Mirror connectivity pre-check prevents silent partial installs.

## Observability hooks
Wrap CLI in your job runner with timers/OTel spans per phase; include `error_code` labels for alerting (`E_DISK`, `E_NET`, …).

## Scaling & containerization
Stateless CLI; mount `./models` volume. Batch jobs for large imports; use `--max-workers` for parallelism. Mirror/offline ready for on-prem.
