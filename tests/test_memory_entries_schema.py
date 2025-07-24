import pytest
from sqlalchemy import create_engine, inspect

from src.ai_karen_engine.database.models import Base, TenantMemoryEntry


class TestMemoryEntriesInitialization:
    def test_create_memory_entries_table(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine, tables=[TenantMemoryEntry.__table__])
        inspector = inspect(engine)
        assert "memory_entries" in inspector.get_table_names()

