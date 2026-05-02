from ai_karen_engine.core.memory.memory_writeback import MemoryWritebackSystem

class _Svc:
    async def commit(self, **kwargs):
        class R: success = True
        return R()

def test_writeback_system_instantiates():
    s = MemoryWritebackSystem(_Svc())
    assert s.writeback_batch_size > 0
