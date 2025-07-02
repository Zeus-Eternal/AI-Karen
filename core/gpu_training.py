"""GPU optimization utilities for neural network training."""

from __future__ import annotations

try:
    import torch
except Exception:  # pragma: no cover - optional dep
    torch = None


def gpu_optimized_train(
    model: "torch.nn.Module",
    dataloader: "torch.utils.data.DataLoader",
    epochs: int = 1,
    lr: float = 1e-3,
    grad_accum_steps: int = 1,
) -> None:
    """Train a model with mixed precision and gradient accumulation on GPU.

    Parameters
    ----------
    model:
        PyTorch model to train.
    dataloader:
        Training dataloader yielding ``(inputs, targets)``.
    epochs:
        Number of full training epochs.
    lr:
        Learning rate for ``AdamW`` optimizer.
    grad_accum_steps:
        Number of steps to accumulate gradients before updating weights.
    """
    if torch is None:
        raise RuntimeError("PyTorch is required for GPU-optimized training")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    scaler = torch.cuda.amp.GradScaler()
    model.train()

    for _ in range(epochs):
        optimizer.zero_grad(set_to_none=True)
        for step, (inputs, targets) in enumerate(dataloader):
            inputs = inputs.to(device)
            targets = targets.to(device)

            with torch.cuda.amp.autocast():
                outputs = model(inputs)
                loss = torch.nn.functional.cross_entropy(outputs, targets)
                loss = loss / grad_accum_steps

            scaler.scale(loss).backward()

            if (step + 1) % grad_accum_steps == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)

        torch.cuda.empty_cache()
