class _Dummy:
    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return None


sidebar = _Dummy()
header = _Dummy()
subheader = _Dummy()
text = _Dummy()
write = _Dummy()
error = _Dummy()


def columns(*args, **kwargs):
    return _Dummy(), _Dummy()


def button(*args, **kwargs):
    return False


session_state = {}


def experimental_rerun(*args, **kwargs):
    return None
