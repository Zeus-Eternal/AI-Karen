from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    open: bool = False


@dataclass(slots=True)
class ExpressionCircuitBreakers:
    failure_threshold: int = 3
    _states: dict[str, CircuitState] = field(default_factory=dict)

    def is_open(self, circuit_id: str) -> bool:
        return self._states.get(circuit_id, CircuitState()).open

    def mark_success(self, circuit_id: str) -> None:
        self._states[circuit_id] = CircuitState(failures=0, open=False)

    def mark_failure(self, circuit_id: str) -> bool:
        state = self._states.get(circuit_id, CircuitState())
        state.failures += 1
        if state.failures >= self.failure_threshold:
            state.open = True
        self._states[circuit_id] = state
        return state.open

