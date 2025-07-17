# SelfRefactor Engine

Kari can improve its own code using the built-in SelfRefactor engine. This component generates patches, runs tests, and stores the results for review. Patches are only merged automatically when the `SRE_AUTO_APPLY` flag is enabled.

The OSIRIS Knowledge Engine feeds the SelfRefactor pipeline. As new information is ingested through multi-hop queries, the engine refreshes its knowledge base and schedules refactor runs, forming a continuous self-updating loop.

## 1. Overview

The engine reads prompts from `self_refactor/prompts/` and uses a local or remote LLM to suggest code improvements. Patches are applied in a sandboxed git worktree and executed with `pytest`. The resulting patch files and test reports are saved under `self_refactor_review/` for manual approval.

### Scheduler

`SREScheduler` periodically launches the engine. The default interval is weekly, but you can trigger a run manually:

```bash
python -m self_refactor.engine --run
```

### Logs

Patch history is stored as sanitized logs. View them via the API:

```bash
curl http://localhost:8000/self_refactor/logs
```

Set `ADVANCED_MODE=true` and add `?full=true` for raw stdout/stderr details.

### Approval Flow

After each run the engine creates a timestamped folder under `self_refactor_review/` containing the generated patches and a `report.json` file with the test results. Review the changes and manually apply them or set the `SRE_AUTO_APPLY=true` environment variable to allow automatic writes to the repository.

## Security Notes

Only admins should enable unrestricted mode. Sanitized logs hide file paths and repository metadata to reduce the risk of leaking sensitive information.
