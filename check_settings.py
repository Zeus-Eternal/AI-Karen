"""Utility script to display key configuration values."""

# ruff: noqa: E402

from pathlib import Path

from dotenv import find_dotenv, load_dotenv  # type: ignore

# Look for environment files relative to this script rather than the
# current working directory so it behaves consistently when executed
# from different locations.
base_dir = Path(__file__).resolve().parent

for name in (".env", ".envK"):
    env_path = find_dotenv(name, usecwd=False) or (base_dir / name)
    if Path(env_path).exists():
        load_dotenv(env_path)

from ai_karen_engine.core.chat_memory_config import settings  # type: ignore

print("database_url =", repr(settings.database_url))
print("redis_url    =", repr(settings.redis_url))
