# NeuroRecall (Labs / Research Harness)

## Boundary
NeuroRecall is **not** a runtime chat memory provider.

NeuroRecall is a **research/evaluation harness** for:
- memory experiments and benchmark runs
- procedural learning candidate discovery
- case-based reasoning evaluation
- judged writeback candidate generation

## Runtime guard
NeuroRecall is disabled for production-runtime import by default.

Enable explicitly for labs only:

```bash
KARI_NEURO_RECALL_LABS_ENABLED=true
```

Default behavior:
- `KARI_NEURO_RECALL_LABS_ENABLED=false` (or unset) blocks runtime imports.

## Approved outputs
NeuroRecall may produce:
- `ProcedureArtifact` candidates
- `LessonArtifact` candidates
- benchmark reports
- recall failure reports
- tool-sequence evaluation traces
- judge scores

NeuroRecall **must not** directly write durable production memory.
All durable persistence must flow through the unified memory writeback review path.

## Notes
After migration/audit completion, this package can be moved to:
- `core/labs/neuro_recall/`, or
- `learning/neuro_recall/`.
