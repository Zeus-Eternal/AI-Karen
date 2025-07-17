import importlib
import sqlite3
import types


def load_manager(monkeypatch):
    real_connect = sqlite3.connect
    monkeypatch.setattr(
        sqlite3,
        "connect",
        lambda *a, **kw: real_connect(":memory:", check_same_thread=False),
    )
    import ai_karen_engine.core.memory.manager as manager

    return importlib.reload(manager)


class DataFrame:
    def __init__(self, records):
        self.records = records

    def to_dict(self, orient):
        return self.records


class DuckCon:
    def __init__(self, store):
        self.store = store
        self._df = None

    def execute(self, sql, params=None):
        sql = sql.strip().upper()
        if sql.startswith("INSERT"):
            self.store.append(
                {
                    "tenant_id": params[0],
                    "user_id": params[1],
                    "session_id": params[2],
                    "query": params[3],
                    "result": params[4],
                    "timestamp": params[5],
                }
            )
            return self
        if sql.startswith("SELECT"):
            limit = params[-1]
            self._df = DataFrame(self.store[:limit])
            return self
        return self

    def fetchdf(self):
        return self._df


def duckdb_stub(store):
    def connect(path, read_only=False):
        return DuckCon(store)

    return types.SimpleNamespace(connect=connect)


class FakeRedisClient:
    def __init__(self):
        self.data = {}

    def lpush(self, key, value):
        self.data.setdefault(key, []).insert(0, value)

    def lrange(self, key, start, end):
        arr = self.data.get(key, [])
        if end == -1:
            end = len(arr) - 1
        return arr[start : end + 1]


class FakeRedisModule:
    def __init__(self):
        self.instance = FakeRedisClient()

    def Redis(self):
        return self.instance


class RecordingPostgres:
    def __init__(self, raise_on_upsert: bool = False) -> None:
        self.raise_on_upsert = raise_on_upsert
        self.upserts = []
        self.recalls = []

    def upsert_memory(
        self,
        vector_id,
        tenant_id,
        user_id,
        session_id,
        query,
        result,
        timestamp,
    ):
        if self.raise_on_upsert:
            raise RuntimeError("db down")
        self.upserts.append((vector_id, tenant_id, user_id, session_id, query, result, timestamp))

    def recall_memory(self, user_id, query, limit, tenant_id=""):
        self.recalls.append((user_id, query, limit, tenant_id))
        return [{"source": "postgres"}]

    def get_by_vector(self, vid):
        return None


def test_recall_priority_order(monkeypatch):
    mm = load_manager(monkeypatch)
    calls = []
    store = []

    class FakeVault:
        def query(self, user_id, q, top_k=10):
            calls.append("neuro")
            return []

    monkeypatch.setattr(mm, "neuro_vault", FakeVault())

    monkeypatch.setattr(mm, "ElasticClient", type("FakeElastic", (), {"__init__": lambda self,*a,**k: None, "search": lambda self, u, q, limit: (calls.append("elastic"), [])[-1]}))
    monkeypatch.setattr(
        mm,
        "recall_vectors",
        lambda u, q, top_k, tenant_id=None: (calls.append("milvus"), [])[-1],
    )
    pg = RecordingPostgres()

    def recall_memory(user_id, query, limit, tenant_id=None):
        calls.append("postgres")
        return []

    pg.recall_memory = recall_memory
    monkeypatch.setattr(mm, "postgres", pg)
    monkeypatch.setattr(
        mm,
        "pg_syncer",
        types.SimpleNamespace(postgres_available=True, mark_unavailable=lambda: None),
    )

    fake_redis = FakeRedisModule()

    def lrange(key, start, end):
        calls.append("redis")
        return []

    fake_redis.instance.lrange = lrange
    monkeypatch.setattr(mm, "redis", fake_redis)
    monkeypatch.setattr(mm, "redis", fake_redis)
    monkeypatch.setattr(mm, "redis", fake_redis)
    monkeypatch.setattr(mm, "get_redis_client", lambda: fake_redis.instance)

    def connect(path, read_only=False):
        calls.append("duckdb")
        return DuckCon(store)

    monkeypatch.setattr(mm, "duckdb", types.SimpleNamespace(connect=connect))

    result = mm.recall_context({"user_id": "u", "tenant_id": "t"}, "q")
    assert result is None
    assert calls == ["neuro", "elastic", "milvus", "postgres", "redis", "duckdb"]


def test_recall_returns_first_available(monkeypatch):
    mm = load_manager(monkeypatch)
    store = []
    calls = []

    class FakeVault:
        def query(self, u, q, top_k=10):
            calls.append("neuro")
            return [{"source": "vault"}]

    monkeypatch.setattr(mm, "neuro_vault", FakeVault())

    monkeypatch.setattr(mm, "ElasticClient", None)

    def mv(u, q, top_k, tenant_id=None):
        calls.append("milvus")
        return [{"source": "milvus"}]

    monkeypatch.setattr(mm, "recall_vectors", mv)
    monkeypatch.setattr(mm, "postgres", RecordingPostgres())
    monkeypatch.setattr(
        mm,
        "pg_syncer",
        types.SimpleNamespace(postgres_available=True, mark_unavailable=lambda: None),
    )
    fake_red = FakeRedisModule()
    monkeypatch.setattr(mm, "redis", fake_red)
    monkeypatch.setattr(mm, "get_redis_client", lambda: fake_red.instance)
    monkeypatch.setattr(mm, "duckdb", duckdb_stub(store))

    result = mm.recall_context({"user_id": "u", "tenant_id": "t"}, "q")
    assert result[0]["source"] == "vault"
    assert calls == ["neuro"]


def test_update_memory_success(monkeypatch):
    mm = load_manager(monkeypatch)
    store = []
    pg = RecordingPostgres()
    fake_redis = FakeRedisModule()

    class FakeVault:
        def index_text(self, *a, **k):
            pass

    monkeypatch.setattr(mm, "neuro_vault", FakeVault())

    monkeypatch.setattr(mm, "postgres", pg)
    monkeypatch.setattr(
        mm,
        "pg_syncer",
        types.SimpleNamespace(postgres_available=True, mark_unavailable=lambda: None),
    )
    monkeypatch.setattr(mm, "get_redis_client", lambda: fake_redis.instance)
    monkeypatch.setattr(mm, "duckdb", duckdb_stub(store))
    monkeypatch.setattr(mm, "store_vector", lambda u, q, r, tenant_id=None: 1)

    ok = mm.update_memory({"user_id": "u", "session_id": "s", "tenant_id": "t"}, "q", "r")
    assert ok
    assert pg.upserts
    assert store


def test_update_memory_postgres_failure(monkeypatch):
    mm = load_manager(monkeypatch)
    store = []
    pg = RecordingPostgres(raise_on_upsert=True)
    fake_redis = FakeRedisModule()

    class FakeVault:
        def index_text(self, *a, **k):
            pass

    monkeypatch.setattr(mm, "neuro_vault", FakeVault())

    monkeypatch.setattr(mm, "postgres", pg)
    monkeypatch.setattr(
        mm,
        "pg_syncer",
        types.SimpleNamespace(postgres_available=True, mark_unavailable=lambda: None),
    )
    monkeypatch.setattr(mm, "get_redis_client", lambda: fake_redis.instance)
    monkeypatch.setattr(mm, "duckdb", duckdb_stub(store))
    monkeypatch.setattr(mm, "store_vector", lambda u, q, r, tenant_id=None: 1)

    ok = mm.update_memory({"user_id": "u", "session_id": "s", "tenant_id": "t"}, "q", "r")
    assert ok
    assert not pg.upserts
    assert store


def test_memory_metrics(monkeypatch):
    mm = load_manager(monkeypatch)
    store = []
    monkeypatch.setattr(mm, "postgres", None)
    fake_redis_mod = FakeRedisModule()
    monkeypatch.setattr(mm, "redis", fake_redis_mod)
    monkeypatch.setattr(mm, "get_redis_client", lambda: fake_redis_mod.instance)
    monkeypatch.setattr(mm, "duckdb", duckdb_stub(store))
    monkeypatch.setattr(mm, "store_vector", lambda u, q, r, tenant_id=None: 1)

    mm.update_memory({"user_id": "u", "session_id": "s", "tenant_id": "t"}, "q", "r")
    mm.recall_context({"user_id": "u", "tenant_id": "t"}, "q")
    assert mm._METRICS["memory_store_total"] > 0
    assert mm._METRICS["memory_recall_total"] > 0


def test_tenant_isolation(monkeypatch):
    mm = load_manager(monkeypatch)
    store = []
    pg = RecordingPostgres()
    def recall_memory(user_id, query, limit, tenant_id=None):
        if tenant_id != "A":
            return []
        return [{"source": "postgres"}]
    pg.recall_memory = recall_memory
    monkeypatch.setattr(mm, "postgres", pg)
    monkeypatch.setattr(mm, "pg_syncer", types.SimpleNamespace(postgres_available=True, mark_unavailable=lambda: None))
    red_mod = FakeRedisModule()
    monkeypatch.setattr(mm, "redis", red_mod)
    monkeypatch.setattr(mm, "get_redis_client", lambda: red_mod.instance)
    monkeypatch.setattr(mm, "duckdb", duckdb_stub(store))
    monkeypatch.setattr(mm, "store_vector", lambda u, q, r, tenant_id=None: 1)

    mm.update_memory({"user_id": "u", "session_id": "s", "tenant_id": "A"}, "q", "r")
    # isolate DuckDB results for tenant B
    monkeypatch.setattr(mm, "duckdb", duckdb_stub([]))
    same = mm.recall_context({"user_id": "u", "tenant_id": "A"}, "q")
    assert same
    res = mm.recall_context({"user_id": "u", "tenant_id": "B"}, "q")
    assert res is None

