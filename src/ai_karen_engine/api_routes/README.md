# AI Karen Engine API Routes

`api_routes/` now follows a grouped public-domain layout instead of a flat route graveyard.

## Layout

```text
api_routes/
├── admin/
├── agents/
├── auth/
├── automation/
├── chat/
├── cognition/
├── content/
├── extensions/
├── knowledge/
├── memory/
├── models/
├── monitoring/
├── optimization/
├── plugins/
├── public/
├── shared/
├── system/
├── tools/
├── training/
└── users/
```

## Notes

- Route modules are thin API surfaces that delegate to services, core systems, and helpers.
- Shared schemas and middleware live under `shared/`.
- `core/gateway/routing.py` now discovers `api_routes` recursively, so nested packages are mounted automatically.
- `server/routers.py` still wires the major app surfaces explicitly where custom prefixes or fallback handling are needed.

## Migration Rule

When adding a route:

1. Put it in the owning domain package.
2. Reuse an existing authority module when the surface overlaps.
3. Keep public endpoint definitions out of support-only modules.
