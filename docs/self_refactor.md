# SelfRefactor Engine

Kari can improve its own code using the built-in SelfRefactor engine. This component generates patches, runs tests, and stores the results for review. Patches are only merged automatically when the `ENABLE_SELF_REFACTOR_AUTO_MERGE` flag is enabled; otherwise they await manual approval.

The OSIRIS Knowledge Engine feeds the SelfRefactor pipeline. As new information is ingested through multi-hop queries, the engine refreshes its knowledge base and schedules refactor runs, forming a continuous self-updating loop.

## 1. Overview

The engine reads prompts from `self_refactor/prompts/` and uses a local or remote LLM to suggest code improvements. Patches are applied in a sandboxed git worktree and executed with `pytest` before merging.

### Scheduler

`SREScheduler` periodically launches the engine. The default interval is weekly, but you can trigger a run manually:

```bash
python -m self_refactor.engine --run
```

### Review Directory

Every run saves proposed patches and their test results under
`self_refactor/reviews/` using a timestamped folder. Review the `report.json`
and patch files before manually applying them. Set
`ENABLE_SELF_REFACTOR_AUTO_MERGE=true` to allow the engine to write changes
directly after tests pass.

### Logs

Patch history is stored as sanitized logs. View them via the API:

```bash
curl http://localhost:8000/self_refactor/logs
```

Set `ADVANCED_MODE=true` and add `?full=true` for raw stdout/stderr details.

## Security Notes

Only admins should enable unrestricted mode. Sanitized logs hide file paths and repository metadata to reduce the risk of leaking sensitive information.
