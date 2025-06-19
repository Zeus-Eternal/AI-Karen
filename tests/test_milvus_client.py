from core.milvus_client import MilvusClient


def test_upsert_and_search():
    client = MilvusClient()
    vec1 = [0.0, 1.0]
    vec2 = [1.0, 0.0]
    client.upsert(vec1, {"text": "first"})
    client.upsert(vec2, {"text": "second"})
    results = client.search([0.0, 0.9], top_k=1)
    assert results[0]["payload"]["text"] == "first"
