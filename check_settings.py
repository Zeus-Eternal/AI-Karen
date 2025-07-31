from pathlib import Path

from dotenv import load_dotenv

if Path(".env").exists():
    load_dotenv(".env")
if Path(".envK").exists():
    load_dotenv(".envK")

from ai_karen_engine.core.chat_memory_config import settings

print("database_url =", repr(settings.database_url))
print("redis_url    =", repr(settings.redis_url))
