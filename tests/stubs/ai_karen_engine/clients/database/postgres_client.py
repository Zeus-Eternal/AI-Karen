import sqlite3

class PostgresClient:
    def __init__(self, dsn: str = "sqlite:///:memory:", use_sqlite: bool = True) -> None:
        path = dsn.replace("sqlite://", "") if dsn.startswith("sqlite://") else ":memory:"
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS memory (vector_id INTEGER PRIMARY KEY, tenant_id TEXT, user_id TEXT, session_id TEXT, query TEXT, result TEXT, timestamp INTEGER)"
        )

    def upsert_memory(
        self, vector_id, tenant_id, user_id, session_id, query, result, timestamp=0
    ):
        self.conn.execute(
            "INSERT OR REPLACE INTO memory(vector_id,tenant_id,user_id,session_id,query,result,timestamp) VALUES (?,?,?,?,?,?,?)",
            (vector_id, tenant_id, user_id, session_id, query, result, timestamp),
        )
        self.conn.commit()

    def get_by_vector(self, vector_id):
        row = self.conn.execute(
            "SELECT tenant_id, user_id, session_id, query, result, timestamp FROM memory WHERE vector_id=?",
            (vector_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "tenant_id": row[0],
            "user_id": row[1],
            "session_id": row[2],
            "query": row[3],
            "result": row[4],
            "timestamp": row[5],
        }

    def get_session_records(self, session_id, tenant_id=None):
        if tenant_id is None:
            rows = self.conn.execute(
                "SELECT vector_id,tenant_id,user_id,session_id,query,result,timestamp FROM memory WHERE session_id=?",
                (session_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT vector_id,tenant_id,user_id,session_id,query,result,timestamp FROM memory WHERE session_id=? AND tenant_id=?",
                (session_id, tenant_id),
            ).fetchall()
        return [
            {
                "vector_id": r[0],
                "tenant_id": r[1],
                "user_id": r[2],
                "session_id": r[3],
                "query": r[4],
                "result": r[5],
                "timestamp": r[6],
            }
            for r in rows
        ]

    def recall_memory(self, user_id, query=None, limit=5, tenant_id=None):
        if tenant_id is None:
            rows = self.conn.execute(
                "SELECT vector_id,tenant_id,user_id,session_id,query,result,timestamp FROM memory WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT vector_id,tenant_id,user_id,session_id,query,result,timestamp FROM memory WHERE user_id=? AND tenant_id=? ORDER BY timestamp DESC LIMIT ?",
                (user_id, tenant_id, limit),
            ).fetchall()
        return [
            {
                "vector_id": r[0],
                "tenant_id": r[1],
                "user_id": r[2],
                "session_id": r[3],
                "query": r[4],
                "result": r[5],
                "timestamp": r[6],
            }
            for r in rows
        ]

    def delete(self, vector_id):
        self.conn.execute("DELETE FROM memory WHERE vector_id=?", (vector_id,))
        self.conn.commit()

    def health(self):
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception:
            return False
