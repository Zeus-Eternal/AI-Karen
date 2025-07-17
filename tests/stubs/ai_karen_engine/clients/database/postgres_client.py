class PostgresClient:
    def __init__(self, dsn: str = "", use_sqlite: bool = True) -> None:
        self._store = {}

    def upsert_memory(self, vector_id, user_id, session_id, query, result, timestamp=0):
        self._store[vector_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "result": result,
            "timestamp": timestamp,
        }

    def get_by_vector(self, vector_id):
        return self._store.get(vector_id)

    def get_session_records(self, session_id):
        return [v for v in self._store.values() if v["session_id"] == session_id]

    def recall_memory(self, user_id, limit=5):
        recs = [v for v in self._store.values() if v["user_id"] == user_id]
        return sorted(recs, key=lambda r: r["timestamp"], reverse=True)[:limit]

    def delete(self, vector_id):
        self._store.pop(vector_id, None)

    def health(self):
        return True
