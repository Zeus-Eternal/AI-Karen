import time
from typing import Any

import pytest  # type: ignore

from ai_karen_engine.core.milvus_client import (  # type: ignore
    MilvusClient,
    _vector_stores,
    recall_vectors,
    store_vector,
)


def setup_function(func: Any) -> None:
    _vector_stores.clear()


def test_upsert_and_search() -> None:
    client = MilvusClient()
    vec1 = [0.0, 1.0]
    vec2 = [1.0, 0.0]
    client.upsert(vec1, {"text": "first", "label": "a"})
    client.upsert(vec2, {"text": "second", "label": "b"})
    results = client.search_sync([0.0, 0.9], top_k=1)
    assert results[0]["payload"]["text"] == "first"


def test_metadata_filter_and_dimension_check() -> None:
    client = MilvusClient(dim=2)
    client.upsert([0.1, 0.2], {"tag": "keep"})
    client.upsert([0.9, 0.1], {"tag": "skip"})
    with pytest.raises(ValueError):
        client.upsert([0.1, 0.2, 0.3], {})
    results = client.search_sync([0.1, 0.2], metadata_filter={"tag": "keep"})
    assert len(results) == 1
    assert results[0]["payload"]["tag"] == "keep"


def test_ttl_pruning() -> None:
    client = MilvusClient(ttl_seconds=0.1)
    client.upsert([0.0, 1.0], {"text": "old"})
    time.sleep(0.2)
    client.upsert([1.0, 0.0], {"text": "new"})
    results = client.search_sync([1.0, 0.0], top_k=3)
    texts = [r["payload"]["text"] for r in results]
    assert "new" in texts
    assert "old" not in texts


def test_delete_removes_ids_and_preserves_dict() -> None:
    client = MilvusClient()
    id1 = client.upsert([0.1, 0.2], {"text": "a"})
    id2 = client.upsert([0.2, 0.1], {"text": "b"})
    id3 = client.upsert([0.3, 0.3], {"text": "c"})
    client.delete_sync([id1, id3])
    assert isinstance(client._data, dict)
    assert id1 not in client._data
    assert id3 not in client._data
    assert id2 in client._data


def test_delete_nonexistent_id_no_error() -> None:
    client = MilvusClient()
    kept = client.upsert([1.0, 0.0], {"text": "keep"})
    client.delete_sync([9999])
    assert kept in client._data


def test_search_cache_populates() -> None:
    client = MilvusClient(cache_size=1)
    vec = [1.0, 0.0]
    client.upsert(vec, {"text": "cached"})
    first = client.search_sync(vec)
    assert len(client._cache) == 1
    second = client.search_sync(vec)
    assert first == second


def test_hnsw_index_search() -> None:
    client = MilvusClient(index_type="hnsw")
    client.upsert([0.0, 1.0], {"text": "first"})
    client.upsert([1.0, 0.0], {"text": "second"})
    results = client.search_sync([0.0, 0.9], top_k=1)
    assert results[0]["payload"]["text"] == "first"


def test_tenant_isolation_store_funcs() -> None:
    store_vector("u", "hello", "ra", tenant_id="A")
    store_vector("u", "hello", "rb", tenant_id="B")
    res_a = recall_vectors("u", "hello", tenant_id="A")
    res_b = recall_vectors("u", "hello", tenant_id="B")
    assert res_a[0]["result"] == "ra"
    assert res_b[0]["result"] == "rb"
