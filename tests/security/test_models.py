from datetime import datetime, timedelta

from ai_karen_engine.security.models import (
    AuthEvent,
    AuthEventType,
    SessionData,
    UserData,
)


def test_user_data_serialization_roundtrip():
    user = UserData(user_id="u1", email="user@example.com")
    data = user.to_dict()
    restored = UserData.from_dict(data)
    assert restored.user_id == user.user_id
    assert restored.email == user.email
    assert restored.created_at is not None


def test_session_data_serialization_and_expiry():
    user = UserData(user_id="u1", email="user@example.com")
    past = datetime.utcnow() - timedelta(seconds=2)
    session = SessionData(
        session_token="s",
        access_token="a",
        refresh_token="r",
        user_data=user,
        expires_in=1,
        created_at=past,
        last_accessed=past,
    )
    data = session.to_dict()
    restored = SessionData.from_dict(data)
    assert restored.session_token == session.session_token
    assert restored.is_expired() is True


def test_auth_event_serialization_roundtrip():
    event = AuthEvent(
        event_type=AuthEventType.LOGIN_ATTEMPT,
        timestamp=datetime.utcnow(),
        user_id="u1",
        success=False,
        error_message="boom",
    )
    data = event.to_dict()
    restored = AuthEvent.from_dict(data)
    assert restored.event_type == AuthEventType.LOGIN_ATTEMPT
    assert restored.error_message == "boom"
