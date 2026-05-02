import pytest
from ai_karen_engine.core.memory.migrations.neuro_vault_migrator import NeuroVaultMigrator

class _WB:
    async def queue_writeback(self, **kwargs):
        return 'id'

@pytest.mark.asyncio
async def test_migrate_entry_counts():
    m = NeuroVaultMigrator(_WB())
    r = await m.migrate_entries([{'id':'1','tenant_id':'t','user_id':'u','content':'x','memory_type':'episodic'}])
    assert r.migrated == 1
