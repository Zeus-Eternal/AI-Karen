#!/usr/bin/env python3
import argparse
import os
import signal
import sys
import time
from pathlib import Path
import subprocess

try:
    import requests  # type: ignore
except Exception:
    requests = None


def read_pid(pidfile: Path) -> int:
    try:
        return int(pidfile.read_text(encoding="utf-8").strip())
    except Exception:
        return -1


def is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def start_manager(args) -> int:
    log_dir = Path(args.log_dir or (Path.cwd() / "logs" / "llamacpp"))
    log_dir.mkdir(parents=True, exist_ok=True)

    manager_pidfile = log_dir / "manager.pid"
    if manager_pidfile.exists():
        pid = read_pid(manager_pidfile)
        if is_alive(pid):
            print(f"Manager already running (PID {pid}).")
            return 0
        else:
            try:
                manager_pidfile.unlink()
            except Exception:
                pass

    env = os.environ.copy()
    if args.config:
        env["LLAMA_CONFIG"] = args.config
    if args.log_dir:
        env["LLAMACPP_LOG_DIR"] = str(log_dir)

    python = sys.executable or "python3"
    cmd = [python, str(Path(__file__).parent / "llama_manager.py")]

    if args.foreground:
        return subprocess.call(cmd, env=env)

    stdout_path = log_dir / "manager.stdout"
    stderr_path = log_dir / "manager.stderr"
    with open(stdout_path, "a", encoding="utf-8") as out, open(stderr_path, "a", encoding="utf-8") as err:
        # Detach: new session if available
        preexec = os.setsid if hasattr(os, "setsid") else None
        p = subprocess.Popen(cmd, stdout=out, stderr=err, env=env, preexec_fn=preexec)
        print(f"Started manager in background (PID {p.pid}). Logs: {stdout_path}, {stderr_path}")
        return 0


def stop_manager(args) -> int:
    log_dir = Path(args.log_dir or (Path.cwd() / "logs" / "llamacpp"))
    manager_pidfile = log_dir / "manager.pid"
    pid = read_pid(manager_pidfile)
    if pid <= 0 or not is_alive(pid):
        print("Manager not running.")
        try:
            if manager_pidfile.exists():
                manager_pidfile.unlink()
        except Exception:
            pass
        return 0

    print(f"Stopping manager (PID {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        print(f"Error sending SIGTERM: {e}")
        return 1

    # Wait a bit for clean shutdown
    for _ in range(30):
        if not is_alive(pid):
            break
        time.sleep(1)
    if is_alive(pid):
        print("Manager did not stop gracefully; sending SIGKILL")
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

    try:
        if manager_pidfile.exists():
            manager_pidfile.unlink()
    except Exception:
        pass
    print("Stopped.")
    return 0


def restart_manager(args) -> int:
    code = stop_manager(args)
    if code != 0:
        return code
    time.sleep(1)
    return start_manager(args)


def status_manager(args) -> int:
    # Read PIDs
    log_dir = Path(args.log_dir or (Path.cwd() / "logs" / "llamacpp"))
    manager_pid = read_pid(log_dir / "manager.pid")
    server_pid = read_pid(log_dir / "llama-server.pid")
    print(f"Manager PID: {manager_pid} ({'alive' if is_alive(manager_pid) else 'dead'})")
    print(f"Server PID:  {server_pid} ({'alive' if is_alive(server_pid) else 'dead'})")

    # Optional health probe
    if args.probe:
        host = args.host or os.getenv("LLAMACPP_HOST", "127.0.0.1")
        port = int(args.port or os.getenv("LLAMACPP_PORT", "8080"))
        url = f"http://{host}:{port}/health"
        if requests is None:
            print("Probe skipped (requests not installed).")
            return 0
        try:
            r = requests.get(url, timeout=3)
            print(f"Health {url}: {r.status_code}")
            try:
                print(r.json())
            except Exception:
                print(r.text[:200])
        except Exception as e:
            print(f"Health probe failed: {e}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Llama.cpp Manager CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="Path to config.json (LLAMA_CONFIG)")
    common.add_argument("--log-dir", help="Log directory (LLAMACPP_LOG_DIR)")

    p_start = sub.add_parser("start", parents=[common], help="Start the manager")
    p_start.add_argument("--foreground", action="store_true", help="Run in foreground")
    p_start.set_defaults(func=start_manager)

    p_stop = sub.add_parser("stop", parents=[common], help="Stop the manager")
    p_stop.set_defaults(func=stop_manager)

    p_restart = sub.add_parser("restart", parents=[common], help="Restart the manager")
    p_restart.set_defaults(func=restart_manager)

    p_status = sub.add_parser("status", parents=[common], help="Show status and optional probe")
    p_status.add_argument("--probe", action="store_true", help="Probe /health of llama-server")
    p_status.add_argument("--host", help="Host for probe (default 127.0.0.1)")
    p_status.add_argument("--port", help="Port for probe (default 8080)")
    p_status.set_defaults(func=status_manager)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

