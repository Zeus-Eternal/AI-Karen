import logging


class SuppressInvalidHTTPFilter(logging.Filter):
    """Filter that suppresses invalid HTTP request log entries.

    Uvicorn may emit noisy log records for malformed or incomplete HTTP
    requests, especially when running behind certain load balancers. This
    filter removes those entries to keep the logs clean.
    """

    INVALID_HTTP_MSG = "Invalid HTTP request received"

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple predicate
        message = record.getMessage()
        return self.INVALID_HTTP_MSG not in message
