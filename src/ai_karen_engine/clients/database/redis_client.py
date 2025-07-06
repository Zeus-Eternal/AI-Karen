"""
RedisClient: Handles volatile short-term memory, cache, session, fast flush.
Production: Use redis-py, thread-safe, supports multiple namespaces.
"""

import redis
import json

class RedisClient:
    def __init__(self, host="localhost", port=6379, db=0, prefix="kari"):
        self.r = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.prefix = prefix

    def _k(self, user_id, kind):
        return f"{self.prefix}:{user_id}:{kind}"

    def flush_short_term(self, user_id):
        """Flush all short-term cache for user."""
        keys = self.r.keys(self._k(user_id, "short_term*"))
        for k in keys:
            self.r.delete(k)

    def flush_long_term(self, user_id):
        """Flush all long-term cache for user."""
        keys = self.r.keys(self._k(user_id, "long_term*"))
        for k in keys:
            self.r.delete(k)

    def set_short_term(self, user_id, data):
        self.r.set(self._k(user_id, "short_term"), json.dumps(data))

    def get_short_term(self, user_id):
        val = self.r.get(self._k(user_id, "short_term"))
        return json.loads(val) if val else None

    def set_session(self, user_id, sess_data):
        self.r.set(self._k(user_id, "session"), json.dumps(sess_data))

    def get_session(self, user_id):
        val = self.r.get(self._k(user_id, "session"))
        return json.loads(val) if val else None

    # Health
    def health(self):
        try:
            self.r.ping()
            return True
        except Exception:
            return False
