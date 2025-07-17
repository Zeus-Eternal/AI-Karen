class RetryError(Exception):
    pass


def retry(*dargs, **dkwargs):
    def decorator(fn):
        return fn
    return decorator


def retry_if_exception_type(exc):
    return None


def stop_after_attempt(attempts):
    return None


def wait_exponential(multiplier=1):
    return None


def nap(seconds):
    pass
