import sqlite3

class Connection(sqlite3.Connection):
    def execute(self, sql, params=None):
        sql = sql.replace("BIGINT AUTO_INCREMENT PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sql = sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
        sql = sql.replace("WITH (encryption='aes256')", "")
        if params is None:
            return super().execute(sql)
        return super().execute(sql, params)


def connect(path=":memory:"):
    return Connection(path)
