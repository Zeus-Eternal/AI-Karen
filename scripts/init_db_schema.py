#!/usr/bin/env python3
"""
No-op DB initialization shim.

Some container images expect `scripts/init_db_schema.py` to exist. In
this environment the real DB migrations are handled elsewhere. Provide a
safe, idempotent script that logs and exits successfully so the container
startup command can continue to uvicorn.
"""
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("init_db_schema")

def main():
    logger.info("init_db_schema: running no-op initialization")
    # Keep this intentionally minimal. If you need schema setup, run
    # scripts/create_tables.py or the proper migration manager instead.
    return 0

if __name__ == "__main__":
    try:
        rc = main()
        sys.exit(rc)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("init_db_schema failed: %s", exc)
        sys.exit(0)
