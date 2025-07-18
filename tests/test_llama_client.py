import asyncio

class DummyEngine:
    def __init__(self):
        self.model = None

    def chat(self, messages, stream=False, **kwargs):
        if stream:
            for t in ['a', 'b']:
                yield t
        else:
            return 'final'

    async def achat(self, messages, stream=False, **kwargs):
        import asyncio
        loop = asyncio.get_event_loop()
        if stream:
            async def generator():
                chunks = await loop.run_in_executor(None, lambda: list(self.chat(messages, stream=True, **kwargs)))
                for c in chunks:
                    yield c
            return generator()
        def _run_sync():
            gen = self.chat(messages, stream=False, **kwargs)
            try:
                return next(gen)
            except StopIteration as ex:
                return ex.value
            except TypeError:
                return gen
        return await loop.run_in_executor(None, _run_sync)

def test_achat_nostream():
    eng = DummyEngine()
    result = asyncio.run(eng.achat([], stream=False))
    assert result == 'final'

def test_achat_stream():
    eng = DummyEngine()
    async def collect():
        gen = await eng.achat([], stream=True)
        return [c async for c in gen]
    chunks = asyncio.run(collect())
    assert chunks == ['a', 'b']
