# Feature: chat-runtime-control-plane-maintenance-restoration, Property 1: Single routing authority
# All chat entry surfaces use the same runtime control decision path

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from ai_karen_engine.core.chat_runtime_control_plane import (
    ChatRuntimeControlPlane,
    RuntimeMode,
    get_chat_runtime_control_plane,
)


@pytest.mark.asyncio
async def test_runtime_control_plane_singleton():
    """Test that get_chat_runtime_control_plane returns a singleton instance."""
    # Reset global instance
    import ai_karen_engine.core.chat_runtime_control_plane as rtcp

    rtcp._runtime_control_plane = None

    plane1 = await get_chat_runtime_control_plane()
    plane2 = await get_chat_runtime_control_plane()

    assert plane1 is plane2
    assert isinstance(plane1, ChatRuntimeControlPlane)


@pytest.mark.asyncio
async def test_runtime_mode_transitions():
    """Test runtime mode transitions are deterministic."""
    plane = ChatRuntimeControlPlane()

    # Test valid transitions
    assert await plane.transition_mode(RuntimeMode.DEGRADED, "test")
    assert await plane.get_current_mode() == RuntimeMode.DEGRADED

    assert await plane.transition_mode(RuntimeMode.MAINTENANCE, "maintenance")
    assert await plane.get_current_mode() == RuntimeMode.MAINTENANCE

    # Test invalid transition (should fail)
    assert not await plane.transition_mode(RuntimeMode.NORMAL, "invalid")
    assert await plane.get_current_mode() == RuntimeMode.MAINTENANCE


@pytest.mark.asyncio
async def test_maintenance_override():
    """Test that maintenance mode overrides all other modes."""
    plane = ChatRuntimeControlPlane()

    # Set normal mode
    await plane.transition_mode(RuntimeMode.NORMAL, "normal")

    # Enable maintenance - should override
    await plane.enable_maintenance("test", "testing", created_by="test")
    assert await plane.get_current_mode() == RuntimeMode.MAINTENANCE

    # Even if we try to set degraded, maintenance should remain
    await plane.transition_mode(RuntimeMode.DEGRADED, "should fail")
    assert await plane.get_current_mode() == RuntimeMode.MAINTENANCE


@pytest.mark.asyncio
async def test_runtime_response_modes():
    """Test that runtime response respects current mode."""
    plane = ChatRuntimeControlPlane()

    # Test normal mode response
    await plane.transition_mode(RuntimeMode.NORMAL, "normal")
    response = await plane.get_runtime_response()
    assert response.get("mode") == "normal"

    # Test maintenance mode response
    await plane.enable_maintenance("test", "testing")
    response = await plane.get_runtime_response()
    assert response.mode == "maintenance"
    assert "maintenance" in response.message.lower()
