# Runtime Mock/Placeholder Inventory (Focused)

## Classification

- **test-only allowed**
  - `tests/**` (Vitest mocks, setup mocks, fixture data).
  - `tests/fixtures/mockFactsApi.ts` moved from production code.
- **dev-only allowed**
  - `src/plugin_repo_backups/**` historical backups not used by production entrypoints.
- **production-path forbidden**
  - Runtime components/adapters under `src/components/**`, `src/lib/**`, `src/app/**`.
  - Backend production paths `core/**`, `api_routes/**`, `services/**` when present.

## Remediation performed

- Removed production mock facts adapter from `src/lib/mockFactsApi.ts` and moved it into `tests/fixtures/mockFactsApi.ts`.
- Replaced Communications Center synthetic outputs with explicit degraded/unavailable states and added degraded telemetry logging (`console.warn` with `[comms-center][degraded]`).
- Added CI guard script: `tools/check-no-prod-mocks.sh` and npm script `ci:forbid-mocks`.
