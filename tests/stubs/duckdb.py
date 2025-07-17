_DBS = {}

def _get_tables(path: str):
    tables = _DBS.setdefault(path, {"session_buffer": []})
    return tables


class DummyConnection:
    def __init__(self, *args, **kwargs):
        self.queries = []
        self.last_query = ""
        self._rows = []
    def cursor(self):
        return self
    def execute(self, query, params=None, *args, **kwargs):
        self.queries.append(query)
        self.last_query = query
        q = query.strip().lower()
        if q.startswith("create table"):
            return self
        if q.startswith("insert into session_buffer"):
            self._tables["session_buffer"].append(list(params))
            return self
        if q.startswith("select count(*) from session_buffer"):
            return self
        if q.startswith("select user_id") or q.startswith("select rowid"):
            sid = params[0]
            self._rows = [row for row in self._tables["session_buffer"] if row[1] == sid]
            return self
        if q.startswith("delete from session_buffer"):
            sid = params[0]
            self._tables["session_buffer"] = [r for r in self._tables["session_buffer"] if r[1] != sid]
            return self
        return self
    def fetchone(self):
        if "count" in self.last_query.lower():
            return (len(self._tables["session_buffer"]),)
        return None
    def fetchall(self):
        if "select user_id" in self.last_query.lower() or "select rowid" in self.last_query.lower():
            return [tuple(row) for row in self._rows]
        return []
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def connect(path="", *_, **__):
    conn = DummyConnection()
    conn._tables = _get_tables(path)
    return conn
