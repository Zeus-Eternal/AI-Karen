# Hydra-Ops Mesh Architecture

This document summarizes the micro-agent "capsule" network used by Kari.

- **Mesh Planner** routes intents to a capsule based on risk scoring.
- **Capsules** bundle persona, tools and guardrails in a folder.
- **Event Bus** pushes incremental events to the UI and metrics collectors.
- **Guardrails** validate tool parameters via a YAML DSL.

See `DEV_SHEET.md` for the full sprint roadmap.
