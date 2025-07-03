from typing import Optional
from pydantic import BaseModel, Field
import os


class ProviderSettings(BaseModel):
    provider: str = Field(default="local", description="LLM provider (local, ollama, openai, etc.)")
    model: str = Field(default="llama3", description="Default model name")
    api_key: Optional[str] = Field(default=None, description="API Key for remote providers")
    base_url: Optional[str] = Field(default=None, description="Base URL for remote provider (if any)")


class MemorySettings(BaseModel):
    enabled: bool = Field(default=True, description="Enable memory system")
    memory_type: str = Field(default="duckdb", description="Memory backend: duckdb, redis, milvus, etc.")
    vector_top_k: int = Field(default=10, description="Top K results to return from vector memory")
    memory_decay: float = Field(default=0.1, description="Exponential decay factor for memory scoring")


class UISettings(BaseModel):
    theme: str = Field(default="dark", description="UI theme")
    language: str = Field(default="en", description="Default UI language")
    notifications: bool = Field(default=True, description="Enable UI notifications")
    max_results: int = Field(default=5, description="Maximum results per panel or section")


class ConfigUI(BaseModel):
    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    ui: UISettings = Field(default_factory=UISettings)

    class Config:
        validate_assignment = True
        extra = "forbid"

    @classmethod
    def load_from_env(cls) -> "ConfigUI":
        return cls(
            provider=ProviderSettings(
                provider=os.getenv("KARI_PROVIDER", "local"),
                model=os.getenv("KARI_MODEL", "llama3"),
                api_key=os.getenv("KARI_API_KEY"),
                base_url=os.getenv("KARI_BASE_URL"),
            ),
            memory=MemorySettings(
                enabled=os.getenv("KARI_MEMORY_ENABLED", "true").lower() == "true",
                memory_type=os.getenv("KARI_MEMORY_TYPE", "duckdb"),
                vector_top_k=int(os.getenv("KARI_VECTOR_TOP_K", 10)),
                memory_decay=float(os.getenv("KARI_MEMORY_DECAY", 0.1)),
            ),
            ui=UISettings(
                theme=os.getenv("KARI_THEME", "dark"),
                language=os.getenv("KARI_LANG", "en"),
                notifications=os.getenv("KARI_NOTIFICATIONS", "true").lower() == "true",
                max_results=int(os.getenv("KARI_MAX_RESULTS", 5)),
            )
        )
