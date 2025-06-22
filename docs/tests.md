# Test Strategy

Kari includes a pytest suite that covers the core API, plugin router and SelfRefactor helpers.

## Test Types

- **Unit Tests** – run quickly and mock external services. Located under `tests/`.
- **Contract Tests** – verify that plugin manifests match the expected schema.
- **End-to-End** – store text and retrieve it via search to ensure the memory layer works.

Run all tests:

```bash
pytest -q
```

Coverage should remain above 85% for core modules.

Chaos tests and performance benchmarks can be added in future phases. See [DEV_SHEET.md](../DEV_SHEET.md) for sprint goals.
