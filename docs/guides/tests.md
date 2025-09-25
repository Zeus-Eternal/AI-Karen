# Test Strategy

Kari includes a pytest suite that covers the core API, plugin router and SelfRefactor helpers.

## Test Types

- **Unit Tests** – run quickly and mock external services. Located under `tests/`.
- **Contract Tests** – verify that plugin manifests match the expected schema.
- **End-to-End** – store text and retrieve it via search to ensure the memory layer works.
- **SaaS Tests** – validate tenant isolation and license enforcement.

Run all tests (the `ai_karen_engine` sources live under `src/` so add it to
`PYTHONPATH` when invoking pytest):

```bash
PYTHONPATH=src pytest -q
```

Coverage should remain above 85% for core modules.

Chaos tests and performance benchmarks can be added in future phases. See [DEV_SHEET.md](../DEV_SHEET.md) for sprint goals.
