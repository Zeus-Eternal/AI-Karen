import pytest
from unittest.mock import AsyncMock, Mock

from ai_karen_engine.services.memory_service import WebUIMemoryService, WebUIMemoryQuery, UISource
from ai_karen_engine.services.memory_service_tenant_wrapper import TenantIsolatedMemoryService
from ai_karen_engine.services.tenant_isolation import SecurityIncidentType, TenantContext


@pytest.fixture
def tenant_service(monkeypatch):
    base = Mock(spec=WebUIMemoryService)
    base.store_web_ui_memory = AsyncMock(return_value="mem-1")
    base.query_memories = AsyncMock(return_value=[])

    mock_tenant = Mock()
    mock_tenant.create_tenant_context.return_value = TenantContext(tenant_id="allowed", user_id="user")
    mock_tenant.validate_data_access.return_value = True
    mock_tenant.log_security_incident = Mock()

    mock_audit = Mock()
    mock_audit.log_memory_create = Mock()
    mock_audit.log_memory_read = Mock()

    monkeypatch.setattr(
        "ai_karen_engine.services.memory_service_tenant_wrapper.get_tenant_isolation_service",
        lambda: mock_tenant,
    )
    monkeypatch.setattr(
        "ai_karen_engine.services.memory_service_tenant_wrapper.get_audit_logger",
        lambda: mock_audit,
    )

    service = TenantIsolatedMemoryService(base)
    return service, base, mock_tenant


@pytest.mark.asyncio
async def test_query_memories_cross_tenant_denied(tenant_service):
    service, base, mock_tenant = tenant_service
    query = WebUIMemoryQuery(text="hi", user_id="user")

    result = await service.query_memories(
        tenant_id="other", query=query, tenant_filters={"user_id": "allowed"}
    )

    assert result == []
    base.query_memories.assert_not_called()
    mock_tenant.log_security_incident.assert_called_once()
    incident = mock_tenant.log_security_incident.call_args.kwargs
    assert incident["incident_type"] == SecurityIncidentType.CROSS_TENANT_ACCESS_ATTEMPT


@pytest.mark.asyncio
async def test_store_memory_cross_tenant_denied(tenant_service):
    service, base, mock_tenant = tenant_service

    with pytest.raises(PermissionError):
        await service.store_web_ui_memory(
            tenant_id="other",
            content="data",
            user_id="user",
            ui_source=UISource.WEB,
            tenant_filters={"user_id": "allowed"},
        )

    base.store_web_ui_memory.assert_not_called()
    mock_tenant.log_security_incident.assert_called()
