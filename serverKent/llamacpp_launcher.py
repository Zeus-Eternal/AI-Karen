#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import socket
from pathlib import Path
import shutil

try:
    import requests  # type: ignore
except Exception:
    requests = None

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "serverKent" / "configs/llamacpp/config.json"
DEFAULT_LOG_DIR = REPO_ROOT / "logs/llamacpp"
SCRIPTS_DIR = REPO_ROOT / "serverKent" / "scripts"


def run(cmd, env=None):
    return subprocess.run(cmd, env=env, check=False)


def print_header(title="Llama.cpp Launcher"):
    os.system("")  # Enable ANSI on Windows terminals
    print("\033[1;36m" + "=" * 64 + "\033[0m")
    print(f"\033[1;36m{title.center(64)}\033[0m")
    print("\033[1;36m" + "=" * 64 + "\033[0m")


def ask(msg, default=None):
    prompt = f"{msg}"
    if default is not None:
        prompt += f" [{default}]"
    prompt += ": "
    val = input(prompt).strip()
    return val if val else default


def load_config(cfg_path: Path) -> dict:
    if not cfg_path.exists():
        return {}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(cfg_path: Path, data: dict):
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def tail_file(path: Path, n=40):
    if not path.exists():
        print(f"No file: {path}")
        return
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-n:]
        for ln in lines:
            print(ln)
    except Exception as e:
        print(f"Error reading {path}: {e}")


def status(config: Path, log_dir: Path):
    print("Manager status:")
    run([sys.executable, str(REPO_ROOT / "serverKent" / "llamacpp_cli.py"), "status", "--log-dir", str(log_dir), "--probe"])  # noqa


def resolve_selected_model(cfg: dict) -> str:
    mp = (cfg or {}).get("model_path") or ""
    # Direct file
    if mp and Path(mp).is_file():
        return str(Path(mp).resolve())
    # Directory selection
    if mp and Path(mp).is_dir():
        cands = sorted(Path(mp).rglob("*.gguf"))
        if cands:
            return str(cands[0].resolve())
    # Auto: pick from discovered models, optionally bias by basename
    prefer = (os.getenv("LLAMACPP_MODEL_BASENAME", "").lower()).strip()
    models = discover_models(cfg)
    if prefer:
        preferred = [m for m in models if Path(m).name.lower().find(prefer) != -1]
        if preferred:
            return preferred[0]
    return models[0] if models else "(unknown)"


def probe_health(host: str, port: int, attempts: int = 60, delay: float = 1.0) -> tuple[int | None, str]:
    url = f"http://{host}:{port}/health"
    code: int | None = None
    body = ""
    for _ in range(max(1, attempts)):
        # HTTP probe if requests available
        if requests is not None:
            try:
                r = requests.get(url, timeout=2)
                code = r.status_code
                body = r.text
                if 200 <= code < 300:
                    break
            except Exception:
                code = None
        else:
            # Fallback: TCP connect
            try:
                with socket.create_connection((host, port), timeout=2):
                    code = 200
                    body = ""
                    break
            except Exception:
                code = None
        time.sleep(delay)
    return code, body


def ensure_server_bin(cfg_path: Path, cfg: dict) -> bool:
    # Prefer env override
    env_bin = os.getenv("LLAMA_SERVER_BIN", "")
    candidates = []
    if env_bin:
        candidates.append(env_bin)
    bin_hint = (cfg or {}).get("server_bin", "llama-server")
    candidates.append(bin_hint)
    # In-repo native
    candidates.append(str(REPO_ROOT / "serverKent" / ".bin" / "llama-server"))
    candidates.append(str(REPO_ROOT / "serverKent" / "system" / "bin" / "llama-server"))
    for b in candidates:
        if not b:
            continue
        p = Path(b)
        if p.exists() and os.access(p, os.X_OK):
            return True
        if shutil.which(b):
            return True
    # Not found; offer to build
    print_header("Server Binary Missing")
    print("llama.cpp server binary not found. You can:")
    print("- Set LLAMA_SERVER_BIN to an absolute path, or")
    print("- Update server_bin in config, or")
    print("- Build native now (recommended).")
    resp = input("Build native llama.cpp now? [Y/n]: ").strip().lower()
    if resp in ("", "y", "yes"):  # build
        rc = run(["bash", str(REPO_ROOT / "serverKent" / "system" / "install_native_llamacpp.sh"), "--gpu", "auto"]).returncode
        return rc == 0
    return False


def discover_search_paths(cfg: dict) -> list:
    paths = []
    paths.extend(cfg.get("model_search_paths", []))
    env_dirs = os.getenv("LLAMACPP_MODEL_DIRS", "")
    if env_dirs:
        paths.extend([p for p in env_dirs.split(os.pathsep) if p])
    paths.extend([
        str(REPO_ROOT / "models"),
        str(REPO_ROOT / "app" / "models"),
        str(REPO_ROOT / "assets" / "models"),
        "/models",
    ])
    # Dedup
    seen = set()
    out = []
    for p in paths:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def discover_models(cfg: dict) -> list:
    models = []
    for root in discover_search_paths(cfg):
        rp = Path(root)
        if not rp.exists():
            continue
        for f in rp.rglob("*.gguf"):
            models.append(str(f))
    models = sorted(models)
    return models


def menu():
    cfg_path = Path(os.getenv("LLAMA_CONFIG", str(DEFAULT_CONFIG)))
    log_dir = Path(os.getenv("LLAMACPP_LOG_DIR", str(DEFAULT_LOG_DIR)))

    while True:
        print_header()
        print("1) Manager: Start")
        print("2) Manager: Stop")
        print("3) Manager: Restart")
        print("4) Manager: Status + Probe")
        print("5) Bare Server: Start")
        print("6) Bare Server: Stop")
        print("7) Logs: Tail manager (last 40)")
        print("8) Logs: Tail server (last 40)")
        print("9) Config: Show path and summary")
        print("10) Config: Set model_path")
        print("11) Config: Set port")
        print("12) Config: Discover models and pick")
        print("13) Config: Set server_bin (llama-server path)")
        print("q) Quit")
        choice = input("Select option: ").strip().lower()

        if choice == "1":
            env = os.environ.copy()
            env["LLAMA_CONFIG"] = str(cfg_path)
            env["LLAMACPP_LOG_DIR"] = str(log_dir)
            cfg = load_config(cfg_path)
            if not ensure_server_bin(cfg_path, cfg):
                print("Aborting start; server binary still missing.")
                time.sleep(0.8)
                continue
            run([str(SCRIPTS_DIR / "llamacpp_service.sh"), "start", "--config", str(cfg_path), "--log-dir", str(log_dir)], env=env)
            # Auto-probe
            host = cfg.get("host", "127.0.0.1")
            port = int(cfg.get("port", 8080))
            selected_model = resolve_selected_model(cfg)
            print_header("Auto Probe")
            print(f"Model: {selected_model}")
            print(f"URL:   http://{host}:{port}")
            code, body = probe_health(host, port)
            print(f"Health: HTTP {code if code is not None else 'no response'}")
            if body:
                print(body[:200])
            time.sleep(0.5)
        elif choice == "2":
            run([str(SCRIPTS_DIR / "llamacpp_service.sh"), "stop", "--log-dir", str(log_dir)])
        elif choice == "3":
            env = os.environ.copy()
            env["LLAMA_CONFIG"] = str(cfg_path)
            env["LLAMACPP_LOG_DIR"] = str(log_dir)
            cfg = load_config(cfg_path)
            if not ensure_server_bin(cfg_path, cfg):
                print("Aborting restart; server binary still missing.")
                time.sleep(0.8)
                continue
            run([str(SCRIPTS_DIR / "llamacpp_service.sh"), "restart", "--config", str(cfg_path), "--log-dir", str(log_dir)], env=env)
            # Auto-probe after restart
            host = cfg.get("host", "127.0.0.1")
            port = int(cfg.get("port", 8080))
            selected_model = resolve_selected_model(cfg)
            print_header("Auto Probe")
            print(f"Model: {selected_model}")
            print(f"URL:   http://{host}:{port}")
            code, body = probe_health(host, port)
            print(f"Health: HTTP {code if code is not None else 'no response'}")
            if body:
                print(body[:200])
            time.sleep(0.5)
        elif choice == "4":
            status(cfg_path, log_dir)
            input("Press Enter to continue...")
        elif choice == "5":
            cfg = load_config(cfg_path)
            model = cfg.get("model_path") or ask("Model path", "./models/llama-cpp/model.gguf")
            host = cfg.get("host", "127.0.0.1")
            port = str(cfg.get("port", 8080))
            threads = str(cfg.get("n_threads", os.cpu_count() or 4))
            ctx = str(cfg.get("n_ctx", 4096))
            ngl = str(cfg.get("n_gpu_layers", 0))
            run([
                str(SCRIPTS_DIR / "llama_bare.sh"), "start",
                "--model", model,
                "--host", host,
                "--port", port,
                "--threads", threads,
                "--ctx", ctx,
                "--ngl", ngl,
                "--log-dir", str(log_dir),
            ])
            time.sleep(0.5)
        elif choice == "6":
            run([str(SCRIPTS_DIR / "llama_bare.sh"), "stop", "--log-dir", str(log_dir)])
        elif choice == "7":
            print_header("Manager Logs (manager.stderr)")
            tail_file(log_dir / "manager.stderr")
            print("\nManager Stdout (tail)")
            tail_file(log_dir / "manager.stdout")
            input("\nPress Enter to continue...")
        elif choice == "8":
            print_header("Server Logs (stderr.log)")
            tail_file(log_dir / "stderr.log")
            print("\nServer Stdout (tail)")
            tail_file(log_dir / "stdout.log")
            input("\nPress Enter to continue...")
        elif choice == "9":
            cfg = load_config(cfg_path)
            print_header("Config Summary")
            print(f"Path: {cfg_path}")
            if cfg:
                print(json.dumps({
                    "model_path": cfg.get("model_path"),
                    "host": cfg.get("host"),
                    "port": cfg.get("port"),
                    "n_ctx": cfg.get("n_ctx"),
                    "n_threads": cfg.get("n_threads"),
                    "n_gpu_layers": cfg.get("n_gpu_layers"),
                    "server_bin": cfg.get("server_bin"),
                    "log_dir": cfg.get("log_dir"),
                }, indent=2))
            else:
                print("Config missing or invalid JSON.")
            input("\nPress Enter to continue...")
        elif choice == "10":
            cfg = load_config(cfg_path)
            current = cfg.get("model_path", "")
            new_path = ask("New model_path", current or "./models/llama-cpp/model.gguf")
            cfg["model_path"] = new_path
            save_config(cfg_path, cfg)
            print("Saved.")
            time.sleep(0.5)
        elif choice == "11":
            cfg = load_config(cfg_path)
            current = str(cfg.get("port", 8080))
            new_port = ask("New port", current)
            try:
                cfg["port"] = int(new_port)
                save_config(cfg_path, cfg)
                print("Saved.")
            except Exception:
                print("Invalid port; not saved.")
            time.sleep(0.5)
        elif choice == "12":
            cfg = load_config(cfg_path)
            models = discover_models(cfg)
            if not models:
                print("No models found in search paths. Configure model_search_paths or LLAMACPP_MODEL_DIRS, or place files under ./models.")
                time.sleep(1.2)
                continue
            print_header("Discovered Models")
            for i, m in enumerate(models, 1):
                print(f"{i:2d}) {m}")
            pick = ask("Pick number", "1")
            try:
                idx = int(pick) - 1
                if idx < 0 or idx >= len(models):
                    raise ValueError
                cfg["model_path"] = models[idx]
                save_config(cfg_path, cfg)
                print("Saved model_path.")
            except Exception:
                print("Invalid selection.")
            time.sleep(0.6)
        elif choice == "13":
            cfg = load_config(cfg_path)
            current = cfg.get("server_bin", os.getenv("LLAMA_SERVER_BIN", "llama-server"))
            new_bin = ask("Path or name for llama-server binary", str(current))
            if new_bin:
                cfg["server_bin"] = new_bin
                save_config(cfg_path, cfg)
                print("Saved server_bin.")
            time.sleep(0.6)
        elif choice in ("q", "quit", "exit"):
            print("Goodbye.")
            return
        else:
            print("Unknown option.")
            time.sleep(0.6)


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupted.")
