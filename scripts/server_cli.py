import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

try:
    import uvicorn
except ModuleNotFoundError:  # pragma: no cover - runtime guard
    print(
        "Error: uvicorn is not installed. Install it with 'pip install uvicorn'",
        file=sys.stderr,
    )
    sys.exit(1)

PID_FILE = Path("server.pid")


def run_server(host: str, port: int, reload: bool = False) -> None:
    """Run the FastAPI server with graceful shutdown."""
    
    local_pkg = Path("fastapi")
    if local_pkg.exists() and local_pkg.is_dir():
        print(
            "Error: a local 'fastapi' directory shadows the FastAPI package.\n"
            "Rename or remove it before starting the server.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = uvicorn.Config("main:app", host=host, port=port, reload=reload)
    server = uvicorn.Server(config)

    def handle_sig(_sig, _frame):
        server.should_exit = True

    signal.signal(signal.SIGTERM, handle_sig)
    signal.signal(signal.SIGINT, handle_sig)

    PID_FILE.write_text(str(os.getpid()))
    try:
        asyncio.run(server.serve())
    finally:
        PID_FILE.unlink(missing_ok=True)


def stop_server() -> None:
    """Stop the running server if the pid file exists."""
    if not PID_FILE.exists():
        print("No running server found")
        return
    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to {pid}")
    except ProcessLookupError:
        print("Server process not running")
    PID_FILE.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Kari backend server")
    sub = parser.add_subparsers(dest="cmd")

    start = sub.add_parser("start", help="start the server")
    start.add_argument("--host", default="0.0.0.0")
    start.add_argument("--port", type=int, default=8000)
    start.add_argument("--reload", action="store_true")

    sub.add_parser("stop", help="stop the server")

    args = parser.parse_args()
    if args.cmd == "start":
        run_server(args.host, args.port, args.reload)
    elif args.cmd == "stop":
        stop_server()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
