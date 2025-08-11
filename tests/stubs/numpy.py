# mypy: ignore-errors
import math

float32 = "float32"
uint8 = "uint8"
inf = float("inf")
nan = float("nan")
__version__ = "0.0"

# Additional numpy types needed for torch compatibility
bool_ = bool
number = float
object_ = object


# Additional numpy attributes
class dtype:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


# Common dtypes
int32 = dtype("int32")
int64 = dtype("int64")
float64 = dtype("float64")


class _Array(list):
    def __getitem__(self, item):
        result = super().__getitem__(item)
        if isinstance(item, slice):
            return _Array(result)
        return result

    def astype(self, dtype):
        if dtype in ("float32", float32):
            return _Array([float(x) for x in self])
        return self

    def __truediv__(self, other):
        return _Array([x / other for x in self])


def array(seq):
    if isinstance(seq, _Array):
        return _Array(seq)
    if any(isinstance(el, (list, tuple, _Array)) for el in seq):
        return [_Array(el) if not isinstance(el, _Array) else el for el in seq]
    return _Array(list(seq))


def frombuffer(buf, dtype=None):
    data = [b for b in buf]
    return _Array(data)


class _Linalg:
    @staticmethod
    def norm(v):
        return math.sqrt(sum(float(x) * float(x) for x in v))


linalg = _Linalg()


def dot(a, b):
    return sum(float(x) * float(y) for x, y in zip(a, b))


def isscalar(num):
    return isinstance(num, (int, float, bool))


def argmax(seq):
    if not seq:
        raise ValueError("argmax of empty sequence")
    max_idx = 0
    max_val = seq[0]
    for i, val in enumerate(seq[1:], 1):
        if val > max_val:
            max_idx, max_val = i, val
    return max_idx


ndarray = _Array
