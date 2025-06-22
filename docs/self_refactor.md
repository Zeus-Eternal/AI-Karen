# SelfRefactor Engine

Kari can improve its own code using the built-in SelfRefactor engine. This component generates patches, runs tests, and merges the changes automatically when they pass.

## 1. Overview

The engine reads prompts from `self_refactor/prompts/` and uses a local or remote LLM to suggest code improvements. Patches are applied in a sandboxed git worktree and executed with `pytest` before merging.

### Scheduler

`SREScheduler` periodically launches the engine. The default interval is weekly, but you can trigger a run manually:

```bash
python -m src.self_refactor.engine --run
```

### Logs

Patch history is stored as sanitized logs. View them via the API:

```bash
curl http://localhost:8000/self_refactor/logs
```

Set `ADVANCED_MODE=true` and add `?full=true` for raw stdout/stderr details.

## Security Notes

Only admins should enable unrestricted mode. Sanitized logs hide file paths and repository metadata to reduce the risk of leaking sensitive information.
