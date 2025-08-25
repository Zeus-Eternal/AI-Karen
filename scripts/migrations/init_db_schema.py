#!/usr/bin/env python3
"""Initialize database schema for AI Karen.

This script validates the PostgreSQL schema and applies automatic
migrations if tables are missing. It should be executed before the
API server starts.
"""

import asyncio
import logging

from ai_karen_engine.database import get_postgres_session
from ai_karen_engine.database.schema_validator import validate_and_migrate_schema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-init")


async def _run() -> None:
    try:
        async with get_postgres_session() as session:
            error = await validate_and_migrate_schema(session)
            if error:
                logger.error("Schema validation failed: %s", error.message)
                raise SystemExit(1)
    except ImportError as exc:
        logger.error("Database dependencies missing: %s", exc)
        raise
    logger.info("Database schema ready")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
