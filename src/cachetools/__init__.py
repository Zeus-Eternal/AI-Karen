import functools
import time


class TTLCache(dict):
    def __init__(self, maxsize=128, ttl=600):
        super().__init__()
        self.maxsize = maxsize
        self.ttl = ttl
        self._expire = {}

    def __setitem__(self, key, value):
        if len(self) >= self.maxsize:
            oldest = min(self._expire, key=lambda k: self._expire[k])
            self.pop(oldest, None)
            self._expire.pop(oldest, None)
        super().__setitem__(key, value)
        self._expire[key] = time.time() + self.ttl

    def __getitem__(self, key):
        if key in self._expire and self._expire[key] < time.time():
            super().pop(key, None)
            self._expire.pop(key, None)
            raise KeyError(key)
        return super().__getitem__(key)

    def pop(self, key, default=None):
        self._expire.pop(key, None)
        return super().pop(key, default)

    def clear(self):
        super().clear()
        self._expire.clear()


def cached(cache):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            try:
                return cache[key]
            except KeyError:
                value = func(*args, **kwargs)
                cache[key] = value
                return value

        return wrapper

    return decorator
