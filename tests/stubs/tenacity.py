class RetryError(Exception):
    pass


def retry(*dargs, **dkwargs):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            attempts = 0
            max_attempts = 3
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    nap(0)
        return wrapped
    return decorator


def retry_if_exception_type(exc):
    return None


def stop_after_attempt(attempts):
    return None


def wait_exponential(multiplier=1):
    return None


def nap(seconds):
    pass
