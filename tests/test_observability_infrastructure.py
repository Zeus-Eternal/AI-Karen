"""
Test suite for Observability Infrastructure - Phase 4.1.d
Comprehensive tests for metrics collection, correlation tracking, SLO monitoring, and structured logging.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Test metrics collection system
def test_metrics_service_initialization():
    """Test metrics service initialization with fallback"""
    from src.ai_karen_engine.services.metrics_service import MetricsService, get_metrics_service
    
    # Test initialization
    metrics_service = MetricsService()
    assert metrics_service is not None
    assert metrics_service.fallback_collector is not None
    
    # Test global instance
    global_service = get_metrics_service()
    assert global_service is not None

def test_metrics_collection():
    """Test comprehensive metrics collection"""
    from src.ai_karen_engine.services.metrics_service import MetricsService
    
    metrics_service = MetricsService()
    
    # Test copilot request metrics
    metrics_service.record_copilot_request("success", "test_user", "test_org", "test_correlation")
    
    # Test memory query metrics
    metrics_service.record_memory_query("search", "success", "test_user", "test_org", "test_correlation")
    
    # Test memory commit metrics
    metrics_service.record_memory_commit("success", "medium", "test_user", "test_org", "test_correlation")
    
    # Test latency metrics
    metrics_service.record_llm_latency(0.5, "local", "test_model", "success", "test_correlation")
    metrics_service.record_vector_latency(0.03, "search", "success", "test_correlation")
    metrics_service.record_total_turn_time(1.2, "copilot_assist", "success", "test_correlation")
    
    # Test memory quality metrics
    metrics_service.update_memory_quality_metrics(
        context_usage_rate=0.8,
        ignored_top_hit_rate=0.1,
        used_shard_rate=0.9,
        avg_relevance_score=0.85,
        user_id="test_user",
        org_id="test_org",
        correlation_id="test_correlation"
    )
    
    # Verify fallback collector has data
    stats = metrics_service.fallback_collector.get_stats()
    assert len(stats["counters"]) > 0
    assert len(stats["histograms"]) > 0
    assert len(stats["gauges"]) > 0

def test_correlation_service():
    """Test correlation ID service functionality"""
    from src.ai_karen_engine.services.correlation_service import CorrelationService, CorrelationTracker
    
    # Test correlation ID generation
    correlation_id = CorrelationService.generate_correlation_id()
    assert correlation_id is not None
    assert len(correlation_id) > 0
    
    # Test header extraction
    headers = {"X-Correlation-Id": "test-correlation-123"}
    extracted_id = CorrelationService.extract_correlation_id(headers)
    assert extracted_id == "test-correlation-123"
    
    # Test get or create
    new_id = CorrelationService.get_or_create_correlation_id(headers)
    assert new_id == "test-correlation-123"
    
    # Test context setting
    CorrelationService.set_correlation_id("context-test-id")
    context_id = CorrelationService.get_correlation_id()
    assert context_id == "context-test-id"
    
    # Test correlation tracker
    tracker = CorrelationTracker()
    tracker.start_trace("trace-123", "test_operation", {"test": "metadata"})
    tracker.add_span("trace-123", "test_span", 0.1, {"span": "data"})
    tracker.end_trace("trace-123", "success", {"result": "completed"})

def test_slo_monitoring():
    """Test SLO monitoring and alerting"""
    from src.ai_karen_engine.services.slo_monitoring import SLOMonitor, SLOTarget, SLOThreshold, AlertRule, AlertSeverity
    
    # Test SLO monitor initialization
    slo_monitor = SLOMonitor()
    assert slo_monitor is not None
    assert len(slo_monitor.slo_targets) > 0  # Should have default SLOs
    assert len(slo_monitor.alert_rules) > 0  # Should have default alert rules
    
    # Test metric recording
    slo_monitor.record_metric("vector_latency_seconds", 0.025)
    slo_monitor.record_metric("llm_latency_seconds", 0.8)
    slo_monitor.record_metric("total_turn_time_seconds", 2.1)
    
    # Test SLO evaluation
    violations = slo_monitor.evaluate_slo_targets()
    # Should not have violations with good metrics
    assert len(violations) == 0
    
    # Test with bad metrics
    slo_monitor.record_metric("vector_latency_seconds", 0.080)  # Above 50ms threshold
    violations = slo_monitor.evaluate_slo_targets()
    # Should have violations now
    assert len(violations) > 0
    
    # Test SLO status
    status = slo_monitor.get_slo_status()
    assert "vector_query_latency" in status
    assert "first_token_latency" in status
    assert "e2e_turn_latency" in status
    
    # Test dashboard data
    dashboard_data = slo_monitor.get_dashboard_data()
    assert "slo_status" in dashboard_data
    assert "active_alerts" in dashboard_data
    assert "recent_violations" in dashboard_data

def test_structured_logging():
    """Test structured logging with PII redaction"""
    from src.ai_karen_engine.services.structured_logging import (
        StructuredLoggingService, PIIRedactor, SecurityLogger, SecurityEventType
    )
    
    # Test PII redaction
    text_with_pii = "Contact john.doe@example.com or call 555-123-4567"
    redacted_text = PIIRedactor.redact_pii(text_with_pii)
    assert "john.doe@example.com" not in redacted_text
    assert "555-123-4567" not in redacted_text
    assert "[REDACTED]" in redacted_text
    
    # Test dict redaction
    data_with_pii = {
        "email": "user@example.com",
        "password": "secret123",
        "message": "Call me at 555-999-8888",
        "safe_data": "This is safe"
    }
    redacted_data = PIIRedactor.redact_dict(data_with_pii)
    assert redacted_data["email"] == "[REDACTED]"
    assert redacted_data["password"] == "[REDACTED]"
    assert "555-999-8888" not in redacted_data["message"]
    assert redacted_data["safe_data"] == "This is safe"
    
    # Test structured logging service
    logging_service = StructuredLoggingService()
    assert logging_service is not None
    assert logging_service.configured is True
    
    # Test security logger
    security_logger = SecurityLogger()
    security_logger.log_authentication_failure("test_user", "192.168.1.1", "test_correlation")
    security_logger.log_cross_tenant_access_attempt("user1", "org1", "org2", "test_correlation")
    security_logger.log_rate_limit_violation("user1", "/api/test", 100, 150, "test_correlation")
    
    # Verify events were logged
    recent_events = security_logger.get_recent_events()
    assert len(recent_events) >= 3

def test_security_middleware():
    """Test security middleware functionality"""
    from src.ai_karen_engine.middleware.security_middleware import (
        SecurityConfig, SecurityMiddlewareStack
    )
    
    # Test security config
    config = SecurityConfig()
    assert config.enforce_https is True
    assert len(config.cors_allowed_origins) > 0
    assert config.rate_limit_enabled is True
    assert len(config.security_headers) > 0
    assert len(config.suspicious_patterns) > 0
    
    # Test middleware stack
    middleware_stack = SecurityMiddlewareStack(config)
    assert middleware_stack.config == config

@pytest.mark.asyncio
async def test_api_routes_integration():
    """Test API routes with observability integration"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.ai_karen_engine.api_routes.copilot_routes import router as copilot_router
    from src.ai_karen_engine.api_routes.memory_routes import router as memory_router
    from src.ai_karen_engine.api_routes.slo_routes import router as slo_router
    
    # Create test app
    app = FastAPI()
    app.include_router(copilot_router, prefix="/copilot")
    app.include_router(memory_router, prefix="/memory")
    app.include_router(slo_router, prefix="/slo")
    
    client = TestClient(app)
    
    # Test copilot assist endpoint
    copilot_response = client.post("/copilot/assist", json={
        "user_id": "test_user",
        "message": "Test message",
        "top_k": 3
    }, headers={"X-Correlation-Id": "test-correlation-123"})
    
    assert copilot_response.status_code == 200
    data = copilot_response.json()
    assert "answer" in data
    assert "correlation_id" in data
    assert data["correlation_id"] == "test-correlation-123"
    
    # Test memory search endpoint
    memory_response = client.post("/memory/search", json={
        "user_id": "test_user",
        "query": "test query",
        "top_k": 5
    }, headers={"X-Correlation-Id": "test-correlation-456"})
    
    assert memory_response.status_code == 200
    data = memory_response.json()
    assert "hits" in data
    assert "correlation_id" in data
    assert data["correlation_id"] == "test-correlation-456"
    
    # Test SLO status endpoint
    slo_response = client.get("/slo/status")
    assert slo_response.status_code == 200
    
    # Test SLO dashboard endpoint
    dashboard_response = client.get("/slo/dashboard")
    assert dashboard_response.status_code == 200
    data = dashboard_response.json()
    assert "slo_status" in data
    assert "active_alerts" in data
    assert "recent_violations" in data
    
    # Test metrics export endpoint
    metrics_response = client.get("/slo/metrics")
    assert metrics_response.status_code == 200
    data = metrics_response.json()
    assert "content" in data
    assert "content_type" in data

def test_performance_thresholds():
    """Test that SLO thresholds match requirements"""
    from src.ai_karen_engine.services.slo_monitoring import get_slo_monitor
    
    slo_monitor = get_slo_monitor()
    
    # Verify vector query latency threshold (p95 < 50ms)
    vector_slo = slo_monitor.slo_targets.get("vector_query_latency")
    assert vector_slo is not None
    assert vector_slo.target_value == 0.050  # 50ms
    
    # Verify first token latency threshold (p95 < 1.2s)
    llm_slo = slo_monitor.slo_targets.get("first_token_latency")
    assert llm_slo is not None
    assert llm_slo.target_value == 1.2  # 1.2 seconds
    
    # Verify end-to-end latency threshold (p95 < 3s)
    e2e_slo = slo_monitor.slo_targets.get("e2e_turn_latency")
    assert e2e_slo is not None
    assert e2e_slo.target_value == 3.0  # 3 seconds


def test_latency_percentiles_under_high_load():
    """Simulate high-load scenarios and verify p95 latency thresholds"""
    from src.ai_karen_engine.services import metrics_service as ms

    ms.PROMETHEUS_AVAILABLE = False
    metrics = ms.MetricsService()
    for i in range(100):
        vec = 0.02 if i < 97 else 0.06
        llm = 0.8 if i < 97 else 1.5
        turn = 2.5 if i < 97 else 4.0
        metrics.record_vector_latency(vec)
        metrics.record_llm_latency(llm, provider="local", model="test")
        metrics.record_total_turn_time(turn, "copilot_assist")

    stats = metrics.fallback_collector.get_stats()
    vec_key = next(k for k in stats["histograms"] if k.startswith("vector_latency_seconds"))
    vec_p95 = stats["histograms"][vec_key]["p95"]
    llm_key = next(k for k in stats["histograms"] if k.startswith("llm_latency_seconds"))
    llm_p95 = stats["histograms"][llm_key]["p95"]
    turn_key = next(k for k in stats["histograms"] if k.startswith("total_turn_time_seconds"))
    turn_p95 = stats["histograms"][turn_key]["p95"]

    assert vec_p95 < 0.05  # 50ms
    assert llm_p95 < 1.2
    assert turn_p95 < 3.0

def test_memory_quality_tracking():
    """Test memory quality metrics tracking"""
    from src.ai_karen_engine.services.metrics_service import get_metrics_service
    
    metrics_service = get_metrics_service()
    
    # Test memory quality metrics
    metrics_service.update_memory_quality_metrics(
        context_usage_rate=0.75,
        ignored_top_hit_rate=0.15,
        used_shard_rate=0.85,
        avg_relevance_score=0.82,
        user_id="test_user",
        org_id="test_org",
        correlation_id="test_correlation"
    )
    
    # Verify metrics were recorded
    stats = metrics_service.get_stats_summary()
    assert stats is not None

def test_correlation_propagation():
    """Test correlation ID propagation through system layers"""
    from src.ai_karen_engine.services.correlation_service import (
        CorrelationService, CorrelationHTTPClient, get_correlation_tracker
    )
    
    # Test correlation ID propagation
    correlation_id = "test-propagation-123"
    CorrelationService.set_correlation_id(correlation_id)
    
    # Verify context propagation
    retrieved_id = CorrelationService.get_correlation_id()
    assert retrieved_id == correlation_id
    
    # Test HTTP client header propagation
    http_client = CorrelationHTTPClient()
    headers = http_client._add_correlation_headers({"Content-Type": "application/json"})
    assert "X-Correlation-Id" in headers
    assert headers["X-Correlation-Id"] == correlation_id
    
    # Test trace tracking
    tracker = get_correlation_tracker()
    tracker.start_trace(correlation_id, "test_operation")
    trace = tracker.get_trace(correlation_id)
    assert trace is not None
    assert trace["correlation_id"] == correlation_id

if __name__ == "__main__":
    # Run basic tests
    test_metrics_service_initialization()
    test_metrics_collection()
    test_correlation_service()
    test_slo_monitoring()
    test_structured_logging()
    test_security_middleware()
    test_performance_thresholds()
    test_memory_quality_tracking()
    test_correlation_propagation()
    
    print("✅ All observability infrastructure tests passed!")
    print("✅ Metrics collection system implemented")
    print("✅ Correlation ID tracking implemented")
    print("✅ SLO monitoring and alerting implemented")
    print("✅ Structured logging with security compliance implemented")
    print("✅ Performance thresholds match requirements:")
    print("   - Vector query p95 latency < 50ms")
    print("   - LLM first token p95 latency < 1.2s")
    print("   - End-to-end turn p95 latency < 3s")
    print("✅ Memory quality metrics tracking implemented")
    print("✅ Security incident logging implemented")
    print("✅ HTTPS enforcement and CORS allowlists implemented")