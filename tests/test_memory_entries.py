import pytest

try:
    from sqlalchemy import create_engine, inspect
    from src.ai_karen_engine.database.models import Base, TenantMemoryItem
    SQLALCHEMY_AVAILABLE = True
except Exception as e:
    SQLALCHEMY_AVAILABLE = False
    import_error = e


@pytest.mark.skipif(not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy not available")
def test_memory_entries_table_creation():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[TenantMemoryItem.__table__])
    inspector = inspect(engine)
    assert "memory_items" in inspector.get_table_names()

