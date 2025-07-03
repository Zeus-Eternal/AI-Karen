# Event Bus

Kari ships with a simple in-memory EventBus that mirrors Redis Streams. Capsules publish events which can be consumed by the Control Room and observability stack.

## API

```python
from src.event_bus import EventBus

bus = EventBus()
msg_id = bus.publish("devops", "deploy", {"status": "ok"}, risk=0.2)
for event in bus.consume():
    print(event.capsule, event.payload)
```

Each `Event` has:

- `id`: unique identifier
- `capsule`: capsule name
- `event_type`: short string
- `payload`: arbitrary JSON data
- `risk`: float used by the mesh planner to prioritize actions

## Hydra-Ops Integration

Capsules emit events when they execute tasks. The mesh planner and guardrail system inspect these events to decide whether to continue or halt a workflow. The desktop UI can subscribe over WebSocket (future work) to show live updates.

See [docs/mesh_arch.md](mesh_arch.md) for the capsule mesh design and [docs/security.md](security.md) for permission considerations.
