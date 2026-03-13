# Worker Agent

A basic worker agent for task execution in the AI-Karen system.

## Capabilities

- Task execution
- Basic reasoning
- Response generation

## Usage

```python
from src.agents.worker_agent.handler import WorkerAgentHandler

handler = WorkerAgentHandler()
result = handler.process_task({"type": "example_task", "data": {"key": "value"}})