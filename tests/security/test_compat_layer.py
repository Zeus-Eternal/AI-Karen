import pytest

from ai_karen_engine.security import compat
from ai_karen_engine.security.auth_service import AuthService, auth_service


@pytest.mark.asyncio
async def test_compat_wrappers_delegate_to_auth_service():
    """Legacy accessors should return the shared AuthService and warn."""

    accessors = [
        compat.get_production_auth_service,
        compat.get_demo_auth_service,
        compat.get_auth_service,
    ]
    emails = ["prod@example.com", "demo@example.com", "generic@example.com"]

    for accessor, email in zip(accessors, emails):
        with pytest.warns(DeprecationWarning):
            service = accessor()
        assert isinstance(service, AuthService)
        # All accessors should return the same singleton instance
        assert service is auth_service()
        # Returned service should expose modern AuthService features
        await service.create_user(email, "password")
        user = await service.authenticate_user(email, "password")
        assert user and user.email == email
