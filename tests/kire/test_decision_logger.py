from ai_karen_engine.routing.decision_logger import DecisionLogger
from ai_karen_engine.routing.types import RouteDecision


def test_decision_logger_history_and_audit():
    dl = DecisionLogger()
    rid = "corr123"
    dl.log_start(rid, user_id="u1", action="routing.select", meta={"task_type": "chat"})
    dec = RouteDecision(
        provider="llamacpp",
        model="tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
        reasoning="test",
        confidence=0.9,
    )
    dl.log_decision(
        request_id=rid,
        user_id="u1",
        task_type="chat",
        khrp_step="output_rendering",
        decision=dec,
        execution_time_ms=12.3,
        success=True,
    )

    hist = dl.get_history(limit=10, user_id="u1")
    assert len(hist) >= 2
    report = dl.generate_audit_report(limit=10)
    assert report["total_events"] >= 2

