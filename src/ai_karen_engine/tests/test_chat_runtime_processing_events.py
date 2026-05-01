from pathlib import Path


def test_chat_runtime_processing_events_strings_present():
    root = Path(__file__).resolve().parents[2] / "ai_karen_engine"
    corpus = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in root.rglob("*.py")
    )

    required = {
        "request_received",
        "runtime_mode_check",
        "auth_context_resolved",
        "session_loaded",
        "conversation_loaded",
        "context_assembly",
        "cortex_start",
        "cortex_complete",
        "memory_recall_start",
        "memory_recall_complete",
        "capsule_recall_start",
        "capsule_recall_complete",
        "provider_selection_start",
        "provider_selected",
        "provider_unavailable",
        "provider_failed",
        "provider_retry",
        "fallback_started",
        "fallback_succeeded",
        "generation_start",
        "response_started",
        "streaming_tokens",
        "post_processing",
        "persistence_start",
        "persistence_complete",
        "memory_writeback_start",
        "memory_writeback_complete",
        "completed",
        "failed",
        "cancelled",
    }
    missing = sorted(event for event in required if event not in corpus)
    assert not missing, f"Missing event labels: {missing}"
