from ai_karen_engine.core.memory.memory_writeback import MemoryWritebackSystem, WritebackEntry, InteractionType

class _Svc:
    async def commit(self, **kwargs):
        class R: success = True
        return R()

def test_profile_fact_candidate():
    s = MemoryWritebackSystem(_Svc())
    e = WritebackEntry(id='1', content='My favorite color is green', interaction_type=InteractionType.USER_QUERY, source_shards=[], user_id='u', org_id='t', session_id=None, correlation_id='c', metadata={'memory_class':'semantic'})
    cs = s._extract_candidates(e)
    assert cs
