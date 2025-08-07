"""
Integration test for the intelligence layer with the consolidated auth system.
"""

import pytest
from datetime import datetime, timedelta

from src.ai_karen_engine.auth import (
    AuthConfig,
    IntelligenceEngine,
    UserData,
    AuthEvent,
    AuthEventType,
    LoginAttempt,
)


@pytest.mark.asyncio
async def test_intelligence_integration():
    """Test that the intelligence engine integrates properly with the auth system."""
    
    # Create configuration with intelligence enabled
    config = AuthConfig()
    config.intelligence.enable_intelligent_auth = True
    config.intelligence.enable_anomaly_detection = True
    config.intelligence.enable_behavioral_analysis = True
    
    # Create intelligence engine
    engine = IntelligenceEngine(config)
    
    # Create sample user data
    user_data = UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    
    # Create sample login attempt
    attempt = LoginAttempt(
        user_id=user_data.user_id,
        email=user_data.email,
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        timestamp=datetime.utcnow(),
        device_fingerprint="device-123",
        geolocation={"latitude": 40.7128, "longitude": -74.0060, "city": "New York"},
    )
    
    # Create sample historical events
    historical_events = []
    base_time = datetime.utcnow() - timedelta(days=30)
    for i in range(15):  # Create 15 events to meet min_training_samples
        event_time = base_time + timedelta(days=i, hours=9 + (i % 8))
        historical_events.append(
            AuthEvent(
                event_type=AuthEventType.LOGIN_SUCCESS,
                timestamp=event_time,
                user_id=user_data.user_id,
                email=user_data.email,
                ip_address=f"192.168.1.{100 + (i % 10)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                success=True,
                details={
                    "device_fingerprint": f"device-{123 + (i % 3)}",
                    "geolocation": {
                        "latitude": 40.7128 + (i % 3) * 0.01,
                        "longitude": -74.0060 + (i % 3) * 0.01,
                        "city": "New York"
                    }
                }
            )
        )
    
    # Test intelligence analysis
    result = await engine.analyze_login_attempt(attempt, user_data, historical_events)
    
    # Verify the result
    assert result is not None
    assert 0.0 <= result.risk_score <= 1.0
    assert result.risk_level in ["low", "medium", "high", "critical"]
    assert isinstance(result.should_block, bool)
    assert isinstance(result.recommendations, list)
    assert result.processing_time_ms > 0
    
    # Test risk score calculation
    context = {
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0",
        "device_fingerprint": "device-123",
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
    }
    
    risk_score = await engine.calculate_risk_score(user_data, context)
    assert 0.0 <= risk_score <= 1.0
    
    print(f"✅ Intelligence integration test passed!")
    print(f"   Risk Score: {result.risk_score:.3f}")
    print(f"   Risk Level: {result.risk_level}")
    print(f"   Should Block: {result.should_block}")
    print(f"   Processing Time: {result.processing_time_ms:.1f}ms")
    print(f"   Recommendations: {len(result.recommendations)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_intelligence_integration())