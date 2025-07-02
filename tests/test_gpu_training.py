import pytest
import importlib

import core.gpu_training as gpu_training


def test_gpu_training_requires_torch():
    if gpu_training.torch is not None:
        pytest.skip("torch installed; environment supports GPU training")
    with pytest.raises(RuntimeError):
        gpu_training.gpu_optimized_train(None, None)
