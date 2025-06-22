# Hydra-Ops Mesh Architecture

This document summarizes the micro-agent "capsule" mesh used by Kari. Capsules are small agents that focus on a domain such as DevOps or Finance.

## Components

- **Mesh Planner** – chooses which capsule should act next based on event risk and guardrail results.
- **Capsules** – folders containing a persona prompt, optional tools and guardrail rules.
- **Event Bus** – publishes capsule events. Consumers stream these events to the UI and metrics.
- **Guardrails** – YAML validators that enforce policy before a capsule executes a tool.

## Risk Matrix

Each event carries a `risk` value between 0.0 and 1.0. The planner prioritizes low‑risk actions and can halt a workflow if the cumulative risk exceeds a threshold.

| Risk | Action |
| ---- | ------ |
| `<0.3` | Auto execute |
| `0.3–0.6` | Require dev approval |
| `>0.6` | Escalate to admin |

See [event_bus.md](event_bus.md) for the event format and [DEV_SHEET.md](../DEV_SHEET.md) for the sprint roadmap.
