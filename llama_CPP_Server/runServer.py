#!/usr/bin/env python3
"""
Entry point for the llama.cpp server.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "_server"))

from _server import (
    LlamaServer,
    ServerConfig,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="llama.cpp server for KAREN")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--host", help="Override host")
    parser.add_argument("--port", type=int, help="Override port")
    parser.add_argument("--log-level", help="Override log level")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = ServerConfig.load(args.config)
    if args.host:
        cfg.data["server"]["host"] = args.host
    if args.port:
        cfg.data["server"]["port"] = args.port
    if args.log_level:
        cfg.data["server"]["log_level"] = args.log_level

    logging.basicConfig(
        level=cfg.get("server.log_level", "info").upper(),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    server = LlamaServer(cfg)
    server.run()


if __name__ == "__main__":
    main()
