from ai_karen_engine.clients.database.elastic_client import ElasticClient


def test_index_and_search_in_memory():
    client = ElasticClient(use_memory=True)
    client.ensure_index()
    entry = {
        "user_id": "u1",
        "session_id": "s1",
        "query": "hello world",
        "result": "r1",
        "timestamp": 1,
    }
    client.index_entry(entry)
    hits = client.search("u1", "hello")
    assert hits and hits[0]["result"] == "r1"


def test_search_no_results():
    client = ElasticClient(use_memory=True)
    client.ensure_index()
    client.index_entry(
        {
            "user_id": "u2",
            "session_id": "s2",
            "query": "foo",
            "result": "bar",
            "timestamp": 1,
        }
    )
    assert client.search("u2", "baz") == []
