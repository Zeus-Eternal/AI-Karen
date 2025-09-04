#!/usr/bin/env python3
"""
Robust Llama.cpp Management Script (portable)
Provides production-ready management of local Llama.cpp instances
with health monitoring, auto-recovery, and performance optimization.

This version prefers user-writable paths by default and allows
overrides via environment variables to avoid requiring root.
"""

import os
import sys
import json
import time
import logging
import signal
import subprocess
import threading
import socket
import shutil
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # Lazily handled if unavailable

try:
    import requests  # type: ignore
    import urllib3  # type: ignore
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:  # pragma: no cover
    requests = None


class LlamaState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"


@dataclass
class LlamaConfig:
    """Configuration for Llama.cpp instance."""
    model_path: str
    host: str = "127.0.0.1"
    port: int = 8080
    n_ctx: int = 2048
    n_threads: int = os.cpu_count() or 4
    n_gpu_layers: int = 0
    verbose: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    timeout: int = 300
    max_retries: int = 3
    health_check_interval: int = 30
    auto_restart: bool = True
    auto_restart_delay: int = 5
    memory_threshold_mb: int = 100
    cpu_threshold_percent: int = 90
    server_bin: str = os.getenv("LLAMA_SERVER_BIN", "llama-server")
    log_dir: str = os.getenv("LLAMACPP_LOG_DIR", str(Path.cwd() / "logs" / "llamacpp"))
    model_search_paths: list = field(default_factory=list)


@dataclass
class LlamaStatus:
    """Current status of Llama.cpp instance."""
    state: LlamaState = LlamaState.STOPPED
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_status: bool = False
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def _build_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("llamacpp-manager")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    fh = logging.FileHandler(log_dir / "manager.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger


class LlamaCppManager:
    """Robust manager for Llama.cpp instances."""

    def __init__(self, config: LlamaConfig):
        self.config = config
        # Prefer user-provided log_dir or fallback to ./logs/llamacpp
        desired_log_dir = Path(self.config.log_dir)
        if not _is_writable_dir(desired_log_dir):
            # Attempt XDG cache as a secondary fallback
            xdg = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "llamacpp"
            if not _is_writable_dir(xdg):
                # Last resort: a temp dir in CWD
                xdg = Path.cwd() / "logs" / "llamacpp"
                _is_writable_dir(xdg)
            self.config.log_dir = str(xdg)

        self.log_dir = Path(self.config.log_dir)
        self.logger = _build_logger(self.log_dir)

        self.status = LlamaStatus()
        self.process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.lock = threading.RLock()

        # PID files
        self.server_pidfile = self.log_dir / "llama-server.pid"
        self.manager_pidfile = self.log_dir / "manager.pid"

        # Resolve/ensure model path exists
        resolved = self._resolve_model_path(self.config.model_path, self._effective_search_paths())
        if resolved is None:
            raise FileNotFoundError(f"Model file not found: {self.config.model_path}")
        self.config.model_path = resolved

    def _effective_search_paths(self) -> list:
        roots = []
        # From config
        roots.extend(self.config.model_search_paths or [])
        # From env (colon-separated)
        env_dirs = os.getenv("LLAMACPP_MODEL_DIRS", "")
        if env_dirs:
            roots.extend([p for p in env_dirs.split(os.pathsep) if p])
        # Common in-app defaults
        defaults = [
            str(Path.cwd() / "models"),
            "/models",
        ]
        roots.extend(defaults)
        # Dedup while preserving order
        seen = set()
        uniq = []
        for r in roots:
            rp = str(Path(r))
            if rp not in seen:
                uniq.append(rp)
                seen.add(rp)
        return uniq

    def _resolve_model_path(self, desired: str, search_paths: list) -> Optional[str]:
        p = Path(desired)
        if desired and p.is_file():
            return str(p)
        # If directory passed, search inside
        if desired and p.is_dir():
            candidates = sorted(Path(desired).rglob("*.gguf"))
            if candidates:
                self.logger.info(f"Resolved model in directory '{desired}' -> '{candidates[0]}'")
                return str(candidates[0])
        # Treat as basename/pattern or 'auto'
        want = (desired or "").lower()
        prefer_name = os.getenv("LLAMACPP_MODEL_BASENAME", "").lower()
        if prefer_name and (not want or want == "auto"):
            want = prefer_name

        found = []
        for root in search_paths:
            rootp = Path(root)
            if not rootp.exists():
                continue
            for f in rootp.rglob("*.gguf"):
                fstr = str(f)
                if not want or want == "auto" or want in f.name.lower():
                    found.append(f)

        if found:
            # Stable sort by path for determinism
            found = sorted(found, key=lambda x: x.as_posix())
            self.logger.info("Discovered models:")
            for f in found[:10]:
                try:
                    sz = f.stat().st_size
                except Exception:
                    sz = 0
                self.logger.info(f" - {f} ({sz//(1024*1024)} MB)")
            self.logger.info(f"Selected model: {found[0]}")
            return str(found[0])
        return None

    def start(self) -> bool:
        """Start the Llama.cpp server."""
        with self.lock:
            if self.status.state in [LlamaState.STARTING, LlamaState.RUNNING]:
                self.logger.warning("Llama.cpp is already starting or running")
                return True

            self.status.state = LlamaState.STARTING
            self.logger.info("Starting Llama.cpp server...")

            try:
                # Resolve server binary early with helpful error if missing
                server_bin = self._resolve_server_bin(self.config.server_bin)
                if server_bin is None:
                    msg = (
                        f"Server binary not found: '{self.config.server_bin}'. "
                        f"Set 'server_bin' in config or export LLAMA_SERVER_BIN to an absolute path."
                    )
                    self.logger.error(msg)
                    self.status.state = LlamaState.FAILED
                    self.status.last_error = msg
                    return False
                # Build command (favor flags supported by most recent versions)
                cmd = [
                    server_bin,
                    "-m", self.config.model_path,
                    "--host", self.config.host,
                    "--port", str(self.config.port),
                    "--ctx-size", str(self.config.n_ctx),
                    "-t", str(self.config.n_threads),  # commonly supported alias for threads
                    "--temp", str(self.config.temperature),
                    "--top-p", str(self.config.top_p),
                    "--top-k", str(self.config.top_k),
                ]

                # Optional flags depending on build
                if self.config.n_gpu_layers > 0:
                    cmd.extend(["-ngl", str(self.config.n_gpu_layers)])  # common alias

                if self.config.timeout:
                    cmd.extend(["--timeout", str(self.config.timeout)])

                if self.config.verbose:
                    cmd.append("--verbose")

                stdout_path = self.log_dir / "stdout.log"
                stderr_path = self.log_dir / "stderr.log"

                # Start process
                self.process = subprocess.Popen(
                    cmd,
                    stdout=open(stdout_path, "a", encoding="utf-8"),
                    stderr=open(stderr_path, "a", encoding="utf-8"),
                    preexec_fn=os.setsid if hasattr(os, "setsid") else None,
                )

                self.status.pid = self.process.pid
                self.status.start_time = datetime.now()

                # Wait for server to be ready
                if self._wait_for_ready():
                    self.status.state = LlamaState.RUNNING
                    self.logger.info(f"Llama.cpp server started successfully (PID: {self.status.pid})")

                    # Write PID files
                    try:
                        self.server_pidfile.write_text(str(self.status.pid), encoding="utf-8")
                        self.manager_pidfile.write_text(str(os.getpid()), encoding="utf-8")
                    except Exception as e:
                        self.logger.warning(f"Could not write pidfiles: {e}")

                    # Start monitoring thread
                    self._start_monitoring()
                    return True
                else:
                    self.status.state = LlamaState.FAILED
                    self.status.last_error = "Failed to start - server not ready"
                    self.logger.error("Llama.cpp server failed to become ready")
                    return False

            except Exception as e:  # pragma: no cover
                self.status.state = LlamaState.FAILED
                self.status.last_error = str(e)
                self.logger.error(f"Failed to start Llama.cpp: {e}")
                return False

    def _resolve_server_bin(self, bin_hint: str) -> Optional[str]:
        # Absolute or relative path provided
        if bin_hint:
            p = Path(bin_hint)
            if p.exists() and os.access(p, os.X_OK):
                return str(p)
        # Try to find in PATH (supports both 'llama-server' and 'server')
        for name in [bin_hint, "llama-server", "server"]:
            if not name:
                continue
            found = shutil.which(name)
            if found:
                return found
        return None

    def stop(self) -> bool:
        """Stop the Llama.cpp server gracefully."""
        with self.lock:
            if self.status.state == LlamaState.STOPPED:
                return True

            self.status.state = LlamaState.STOPPING
            self.logger.info("Stopping Llama.cpp server...")

            # Signal monitoring thread to stop
            self.shutdown_event.set()

            try:
                if self.process:
                    # Try graceful termination
                    self.process.terminate()

                    # Wait for process to terminate
                    try:
                        self.process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Process did not terminate gracefully, forcing kill")
                        self.process.kill()
                        self.process.wait()

                self.status.state = LlamaState.STOPPED
                self.status.pid = None
                self.logger.info("Llama.cpp server stopped successfully")
                # Remove PID files
                try:
                    if self.server_pidfile.exists():
                        self.server_pidfile.unlink()
                    if self.manager_pidfile.exists():
                        self.manager_pidfile.unlink()
                except Exception:
                    pass
                return True

            except Exception as e:  # pragma: no cover
                self.logger.error(f"Error stopping Llama.cpp: {e}")
                return False

    def restart(self) -> bool:
        """Restart the Llama.cpp server."""
        self.logger.info("Restarting Llama.cpp server...")
        if self.stop():
            time.sleep(self.config.auto_restart_delay)
            return self.start()
        return False

    def _http_ok(self, url: str, method: str = "GET", timeout: float = 5.0) -> bool:
        if requests is None:
            return False
        try:
            if method.upper() == "POST":
                r = requests.post(url, timeout=timeout, verify=False)
            else:
                r = requests.get(url, timeout=timeout, verify=False)
            return 200 <= r.status_code < 300
        except Exception:
            return False

    def health_check(self) -> bool:
        """Perform health check on the Llama.cpp server."""
        start_time = time.time()
        ok = False
        # Most builds support GET /health
        ok = ok or self._http_ok(f"http://{self.config.host}:{self.config.port}/health", "GET", 5)
        # Some builds may return 200 on /
        ok = ok or self._http_ok(f"http://{self.config.host}:{self.config.port}/", "GET", 3)
        # Fallback: TCP connect
        if not ok:
            try:
                with socket.create_connection((self.config.host, self.config.port), timeout=2):
                    ok = True
            except Exception:
                ok = False

        response_time_ms = (time.time() - start_time) * 1000
        self.status.last_health_check = datetime.now()
        self.status.health_status = ok
        if ok:
            if self.status.total_requests > 0:
                self.status.avg_response_time = (
                    (self.status.avg_response_time * self.status.total_requests)
                    + response_time_ms
                ) / (self.status.total_requests + 1)
            else:
                self.status.avg_response_time = response_time_ms
            self.status.total_requests += 1
        else:
            self.status.failed_requests += 1
        return ok

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics and status."""
        with self.lock:
            # Get process metrics if running
            if self.status.pid and self.status.state == LlamaState.RUNNING and psutil is not None:
                try:
                    process = psutil.Process(self.status.pid)
                    self.status.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                    self.status.cpu_percent = process.cpu_percent(interval=0.1)
                except Exception:
                    self.status.state = LlamaState.FAILED
                    self.status.last_error = "Process not found or psutil error"

            return {
                "state": self.status.state.value,
                "pid": self.status.pid,
                "start_time": self.status.start_time.isoformat() if self.status.start_time else None,
                "last_health_check": self.status.last_health_check.isoformat() if self.status.last_health_check else None,
                "health_status": self.status.health_status,
                "memory_usage_mb": round(self.status.memory_usage_mb, 2),
                "cpu_percent": round(self.status.cpu_percent, 2),
                "total_requests": self.status.total_requests,
                "failed_requests": self.status.failed_requests,
                "avg_response_time": round(self.status.avg_response_time, 2),
                "last_error": self.status.last_error,
                "config": {
                    "model": Path(self.config.model_path).name,
                    "host": self.config.host,
                    "port": self.config.port,
                    "context_size": self.config.n_ctx,
                    "server_bin": self._resolve_server_bin(self.config.server_bin) or self.config.server_bin,
                },
            }

    def _wait_for_ready(self, timeout: int = 60) -> bool:
        """Wait for server to become ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.health_check():
                return True
            time.sleep(1)
        return False

    def _start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.shutdown_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Started monitoring thread")

    def _monitor_loop(self):
        """Main monitoring loop."""
        consecutive_failures = 0

        while not self.shutdown_event.is_set():
            try:
                is_healthy = self.health_check()

                if is_healthy:
                    consecutive_failures = 0

                    # Check resource usage
                    metrics = self.get_metrics()
                    if (
                        metrics["memory_usage_mb"] > self.config.memory_threshold_mb
                        or metrics["cpu_percent"] > self.config.cpu_threshold_percent
                    ):
                        self.logger.warning(
                            f"High resource usage - Memory: {metrics['memory_usage_mb']}MB, "
                            f"CPU: {metrics['cpu_percent']}%"
                        )
                        self.status.state = LlamaState.DEGRADED
                    else:
                        self.status.state = LlamaState.RUNNING

                else:
                    consecutive_failures += 1
                    self.logger.warning(
                        f"Health check failed ({consecutive_failures} consecutive failures)"
                    )

                    # Auto-restart if configured
                    if self.config.auto_restart and consecutive_failures >= self.config.max_retries:
                        self.logger.error("Max health check failures reached, restarting...")
                        self.restart()
                        consecutive_failures = 0

                # Wait for next check
                self.shutdown_event.wait(self.config.health_check_interval)

            except Exception as e:  # pragma: no cover
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config.health_check_interval)

    def __del__(self):  # pragma: no cover
        try:
            self.stop()
        except Exception:
            pass


def load_config(config_path: Optional[str] = None) -> LlamaConfig:
    """Load configuration from file or use defaults."""
    default_model = os.getenv("LLAMACPP_MODEL", str(Path.cwd() / "models"))
    default_config = LlamaConfig(
        model_path=default_model,
        host=os.getenv("LLAMACPP_HOST", "127.0.0.1"),
        port=int(os.getenv("LLAMACPP_PORT", "8080")),
        n_ctx=int(os.getenv("LLAMACPP_N_CTX", "4096")),
        n_threads=os.cpu_count() or 4,
        n_gpu_layers=int(os.getenv("LLAMACPP_N_GPU", "0")),
        server_bin=os.getenv("LLAMA_SERVER_BIN", "llama-server"),
        log_dir=os.getenv("LLAMACPP_LOG_DIR", str(Path.cwd() / "logs" / "llamacpp")),
        model_search_paths=[p for p in os.getenv("LLAMACPP_MODEL_DIRS", "").split(os.pathsep) if p],
    )

    cfg_path = (
        Path(config_path)
        if config_path
        else Path(os.getenv("LLAMA_CONFIG", str(Path.cwd() / "serverKent" / "configs" / "llamacpp" / "config.json")))
    )

    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            return LlamaConfig(
                model_path=config_data.get("model_path", default_config.model_path),
                host=config_data.get("host", default_config.host),
                port=config_data.get("port", default_config.port),
                n_ctx=config_data.get("n_ctx", default_config.n_ctx),
                n_threads=config_data.get("n_threads", default_config.n_threads),
                n_gpu_layers=config_data.get("n_gpu_layers", default_config.n_gpu_layers),
                verbose=config_data.get("verbose", default_config.verbose),
                temperature=config_data.get("temperature", default_config.temperature),
                top_p=config_data.get("top_p", default_config.top_p),
                top_k=config_data.get("top_k", default_config.top_k),
                timeout=config_data.get("timeout", default_config.timeout),
                max_retries=config_data.get("max_retries", default_config.max_retries),
                health_check_interval=config_data.get("health_check_interval", default_config.health_check_interval),
                auto_restart=config_data.get("auto_restart", default_config.auto_restart),
                auto_restart_delay=config_data.get("auto_restart_delay", default_config.auto_restart_delay),
                memory_threshold_mb=config_data.get("memory_threshold_mb", default_config.memory_threshold_mb),
                cpu_threshold_percent=config_data.get("cpu_threshold_percent", default_config.cpu_threshold_percent),
                # Environment takes precedence over config for server_bin
                server_bin=os.getenv("LLAMA_SERVER_BIN", config_data.get("server_bin", default_config.server_bin)),
                log_dir=config_data.get("log_dir", default_config.log_dir),
                model_search_paths=config_data.get("model_search_paths", default_config.model_search_paths),
            )
        except Exception as e:  # pragma: no cover
            # Fall back to defaults and log to stdout for visibility
            logger = _build_logger(Path(default_config.log_dir))
            logger.error(f"Error loading config file '{cfg_path}': {e}. Using defaults.")
            return default_config
    else:
        # No config file found; use defaults
        logger = _build_logger(Path(default_config.log_dir))
        logger.info(f"No config file found at {cfg_path}, using default configuration")
        return default_config


def signal_handler(signum, _frame):  # pragma: no cover
    logger = logging.getLogger("llamacpp-manager")
    logger.info(f"Received signal {signum}, shutting down...")
    if "manager" in globals():
        try:
            globals()["manager"].stop()
        except Exception:
            pass
    sys.exit(0)


def main():
    # Register signal handlers
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        # Some environments (e.g., Windows threads) may not allow this
        pass

    # Load configuration
    config_path = os.getenv("LLAMA_CONFIG")
    config = load_config(config_path)

    # Create manager instance
    global manager
    manager = LlamaCppManager(config)

    # Start the server
    if not manager.start():
        manager.logger.error("Failed to start Llama.cpp server")
        sys.exit(1)

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.logger.info("Shutting down by user request...")
        manager.stop()


if __name__ == "__main__":
    main()
