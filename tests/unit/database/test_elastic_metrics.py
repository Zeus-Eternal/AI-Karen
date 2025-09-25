from ai_karen_engine.clients.database.elastic_client import ElasticClient, _METRICS


def test_elastic_metrics():
    client = ElasticClient(use_memory=True)
    client.index_entry({'user_id': 'u', 'query': 'q', 'result': 'r', 'timestamp': 0})
    res = client.search('u', 'q')
    assert res
    assert _METRICS['document_index_total'] > 0
    assert _METRICS['document_search_total'] > 0


