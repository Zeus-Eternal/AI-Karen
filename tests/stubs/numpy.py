import math
from types import SimpleNamespace

class ndarray(list):
    def astype(self, _):
        return self

    def __truediv__(self, val):
        return ndarray([x / val for x in self])


def frombuffer(buf, dtype=None):
    return ndarray(buf)


def array(seq, dtype=None):
    return ndarray(seq)


class linalg(SimpleNamespace):
    @staticmethod
    def norm(vec):
        return math.sqrt(sum(float(x) * float(x) for x in vec))


uint8 = "uint8"
float32 = "float32"
