# Event Bus

Kari ships with an in-memory `EventBus` and an optional `RedisEventBus` that uses Redis Streams. Capsules publish events which can be consumed by the Control Room and observability stack.

## API

```python
from ai_karen_engine.event_bus import EventBus

bus = EventBus()
msg_id = bus.publish(
    "devops",
    "deploy",
    {"status": "ok"},
    risk=0.2,
    roles=["admin"],
    tenant_id="acme",
)
for event in bus.consume(["admin"], tenant_id="acme"):
    print(event.capsule, event.payload)
```

Each `Event` has:

- `id`: unique identifier
- `capsule`: capsule name
- `event_type`: short string
- `payload`: arbitrary JSON data
- `risk`: float used by the mesh planner to prioritize actions

## Configuration

`get_event_bus()` chooses the backend based on the `event_bus` key in
`config.json`. Set it to `"redis"` to enable the Redis-backed bus or
`"memory"` for the default in-memory implementation. If Redis is unavailable,
the system automatically falls back to the in-memory bus.

## Hydra-Ops Integration

Capsules emit events when they execute tasks. The mesh planner and guardrail system inspect these events to decide whether to continue or halt a workflow. The desktop UI can subscribe over WebSocket (future work) to show live updates. Events can optionally reference ReasoningGraph nodes for multi-hop decisions.

See [docs/mesh_arch.md](mesh_arch.md) for the capsule mesh design and [docs/security.md](security.md) for permission considerations.
