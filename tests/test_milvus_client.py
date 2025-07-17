import time
import pytest
from ai_karen_engine.core.milvus_client import (
    MilvusClient,
    store_vector,
    recall_vectors,
    _vector_stores,
)


def setup_function(func):
    _vector_stores.clear()


def test_upsert_and_search():
    client = MilvusClient()
    vec1 = [0.0, 1.0]
    vec2 = [1.0, 0.0]
    client.upsert(vec1, {"text": "first", "label": "a"})
    client.upsert(vec2, {"text": "second", "label": "b"})
    results = client.search([0.0, 0.9], top_k=1)
    assert results[0]["payload"]["text"] == "first"


def test_metadata_filter_and_dimension_check():
    client = MilvusClient(dim=2)
    client.upsert([0.1, 0.2], {"tag": "keep"})
    client.upsert([0.9, 0.1], {"tag": "skip"})
    with pytest.raises(ValueError):
        client.upsert([0.1, 0.2, 0.3], {})
    results = client.search([0.1, 0.2], metadata_filter={"tag": "keep"})
    assert len(results) == 1
    assert results[0]["payload"]["tag"] == "keep"


def test_ttl_pruning():
    client = MilvusClient(ttl_seconds=0.1)
    client.upsert([0.0, 1.0], {"text": "old"})
    time.sleep(0.2)
    client.upsert([1.0, 0.0], {"text": "new"})
    results = client.search([1.0, 0.0], top_k=3)
    texts = [r["payload"]["text"] for r in results]
    assert "new" in texts
    assert "old" not in texts


def test_delete_removes_ids_and_preserves_dict():
    client = MilvusClient()
    id1 = client.upsert([0.1, 0.2], {"text": "a"})
    id2 = client.upsert([0.2, 0.1], {"text": "b"})
    id3 = client.upsert([0.3, 0.3], {"text": "c"})
    client.delete([id1, id3])
    assert isinstance(client._data, dict)
    assert id1 not in client._data
    assert id3 not in client._data
    assert id2 in client._data


def test_delete_nonexistent_id_no_error():
    client = MilvusClient()
    kept = client.upsert([1.0, 0.0], {"text": "keep"})
    client.delete([9999])
    assert kept in client._data


def test_tenant_isolation_store_funcs():
    id_a = store_vector("u", "hello", "ra", tenant_id="A")
    id_b = store_vector("u", "hello", "rb", tenant_id="B")
    res_a = recall_vectors("u", "hello", tenant_id="A")
    ids = {r["id"] for r in res_a}
    assert id_a in ids and id_b not in ids
