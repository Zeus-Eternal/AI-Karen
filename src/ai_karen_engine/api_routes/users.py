import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_karen_engine.clients.database.duckdb_client import DuckDBClient
from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.errors import ErrorCode, ErrorResponse
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic
from ai_karen_engine.auth.service import AuthService, get_auth_service
from ai_karen_engine.auth.exceptions import (
    AuthError,
    UserNotFoundError,
    UserAlreadyExistsError,
    RateLimitExceededError,
    SecurityError,
)

APIRouter, Depends, HTTPException, Response = import_fastapi(
    "APIRouter", "Depends", "HTTPException", "Response"
)
BaseModel = import_pydantic("BaseModel")

router = APIRouter()

# Shared DuckDB client instance for dependency injection (for backward compatibility)
_db_client = DuckDBClient()

# Global auth service instance (will be initialized lazily)
auth_service_instance: AuthService = None


def get_db() -> DuckDBClient:
    """Dependency that provides a DuckDB client instance."""
    return _db_client


async def get_auth_service_instance() -> AuthService:
    """Get the auth service instance, initializing it if necessary."""
    global auth_service_instance
    if auth_service_instance is None:
        auth_service_instance = await get_auth_service()
    return auth_service_instance


def http_error(status_code: int, code: ErrorCode, message: str) -> None:
    error = ErrorResponse(
        error_code=code,
        message=message,
        timestamp=datetime.utcnow().isoformat(),
    )
    raise HTTPException(status_code=status_code, detail=error.model_dump())


ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


class UserProfile(BaseModel):
    user_id: str
    name: str | None = None
    email: str | None = None
    preferences: Dict[str, Any] = {}


class CreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    tenant_id: str = "default"
    roles: Optional[List[str]] = None


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    tenant_id: str
    roles: List[str]
    preferences: Dict[str, Any]
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: str


@router.get(
    "/users/{user_id}/profile",
    response_model=UserProfile,
    status_code=200,
    responses=ERROR_RESPONSES,
)
async def get_profile(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
    db: DuckDBClient = Depends(get_db),
) -> UserProfile:
    # Only allow access to own profile or for admin roles
    if current_user.get("user_id") != user_id and "admin" not in current_user.get(
        "roles", []
    ):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to access this profile")

    profile = await asyncio.to_thread(db.get_profile, user_id)
    if profile is None:
        http_error(404, ErrorCode.NOT_FOUND, "Profile not found")
    return UserProfile(user_id=user_id, **profile)


@router.put(
    "/users/{user_id}/profile",
    response_model=UserProfile,
    status_code=200,
    responses=ERROR_RESPONSES,
)
async def save_profile(
    user_id: str,
    profile: UserProfile,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
    db: DuckDBClient = Depends(get_db),
) -> UserProfile:
    # Only allow modifications to own profile or for admin roles
    if current_user.get("user_id") != user_id and "admin" not in current_user.get(
        "roles", []
    ):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to modify this profile")

    data = profile.dict(exclude={"user_id"})
    await asyncio.to_thread(db.save_profile, user_id, data)
    return UserProfile(user_id=user_id, **data)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
)
async def create_user(
    request: CreateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
) -> UserResponse:
    """Create a new user (admin only)."""
    # Only allow admin users to create new users
    if "admin" not in current_user.get("roles", []):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to create users")

    try:
        auth_service = await get_auth_service_instance()
        user_data = await auth_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            tenant_id=request.tenant_id,
            roles=request.roles or ["user"],
        )

        return UserResponse(
            user_id=user_data.user_id,
            email=user_data.email,
            full_name=getattr(user_data, 'full_name', None),
            tenant_id=user_data.tenant_id,
            roles=user_data.roles,
            preferences=getattr(user_data, 'preferences', {}),
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            created_at=user_data.created_at.isoformat(),
            updated_at=user_data.updated_at.isoformat(),
        )

    except UserAlreadyExistsError as e:
        http_error(409, ErrorCode.VALIDATION_ERROR, str(e))
    except RateLimitExceededError as e:
        http_error(429, ErrorCode.RATE_LIMIT_EXCEEDED, str(e))
    except SecurityError as e:
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, str(e))
    except AuthError as e:
        http_error(400, ErrorCode.SERVICE_ERROR, str(e))
    except Exception:
        http_error(500, ErrorCode.INTERNAL_ERROR, "Failed to create user")


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=200,
    responses=ERROR_RESPONSES,
)
async def get_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
) -> UserResponse:
    """Get user details (own profile or admin only)."""
    # Only allow access to own profile or for admin roles
    if current_user.get("user_id") != user_id and "admin" not in current_user.get(
        "roles", []
    ):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to access this user")

    try:
        auth_service = await get_auth_service_instance()
        user_data = await auth_service.get_user_by_id(user_id)

        if not user_data:
            http_error(404, ErrorCode.NOT_FOUND, "User not found")

        return UserResponse(
            user_id=user_data.user_id,
            email=user_data.email,
            full_name=getattr(user_data, 'full_name', None),
            tenant_id=user_data.tenant_id,
            roles=user_data.roles,
            preferences=getattr(user_data, 'preferences', {}),
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            created_at=user_data.created_at.isoformat(),
            updated_at=user_data.updated_at.isoformat(),
        )

    except UserNotFoundError:
        http_error(404, ErrorCode.NOT_FOUND, "User not found")
    except AuthError as e:
        http_error(400, ErrorCode.SERVICE_ERROR, str(e))
    except Exception:
        http_error(500, ErrorCode.INTERNAL_ERROR, "Failed to get user")


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=200,
    responses=ERROR_RESPONSES,
)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
) -> UserResponse:
    """Update user details (own profile or admin only)."""
    # Only allow modifications to own profile or for admin roles
    # Admin can modify roles, regular users cannot
    if current_user.get("user_id") != user_id and "admin" not in current_user.get(
        "roles", []
    ):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to modify this user")

    # Only admin can modify roles and is_active status
    if (request.roles is not None or request.is_active is not None) and "admin" not in current_user.get("roles", []):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to modify user roles or status")

    try:
        auth_service = await get_auth_service_instance()
        
        # Get current user data
        user_data = await auth_service.get_user_by_id(user_id)
        if not user_data:
            http_error(404, ErrorCode.NOT_FOUND, "User not found")

        # Update user data using the consolidated service
        updated_user = await auth_service.update_user(
            user_id=user_id,
            full_name=request.full_name,
            roles=request.roles,
            preferences=request.preferences,
            is_active=request.is_active,
        )

        return UserResponse(
            user_id=updated_user.user_id,
            email=updated_user.email,
            full_name=getattr(updated_user, 'full_name', None),
            tenant_id=updated_user.tenant_id,
            roles=updated_user.roles,
            preferences=getattr(updated_user, 'preferences', {}),
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            created_at=updated_user.created_at.isoformat(),
            updated_at=updated_user.updated_at.isoformat(),
        )

    except UserNotFoundError:
        http_error(404, ErrorCode.NOT_FOUND, "User not found")
    except SecurityError as e:
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, str(e))
    except AuthError as e:
        http_error(400, ErrorCode.SERVICE_ERROR, str(e))
    except Exception:
        http_error(500, ErrorCode.INTERNAL_ERROR, "Failed to update user")


@router.delete(
    "/users/{user_id}",
    status_code=204,
    responses=ERROR_RESPONSES,
)
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_context),
) -> Response:
    """Delete a user (admin only)."""
    # Only allow admin users to delete users
    if "admin" not in current_user.get("roles", []):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to delete users")

    # Prevent self-deletion
    if current_user.get("user_id") == user_id:
        http_error(400, ErrorCode.VALIDATION_ERROR, "Cannot delete your own account")

    try:
        auth_service = await get_auth_service_instance()
        success = await auth_service.delete_user(user_id)

        if not success:
            http_error(404, ErrorCode.NOT_FOUND, "User not found")

        return Response(status_code=204)

    except UserNotFoundError:
        http_error(404, ErrorCode.NOT_FOUND, "User not found")
    except SecurityError as e:
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, str(e))
    except AuthError as e:
        http_error(400, ErrorCode.SERVICE_ERROR, str(e))
    except Exception:
        http_error(500, ErrorCode.INTERNAL_ERROR, "Failed to delete user")


@router.get(
    "/users",
    response_model=List[UserResponse],
    status_code=200,
    responses=ERROR_RESPONSES,
)
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_user_context),
    tenant_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[UserResponse]:
    """List users (admin only)."""
    # Only allow admin users to list users
    if "admin" not in current_user.get("roles", []):
        http_error(403, ErrorCode.AUTHORIZATION_ERROR, "Not authorized to list users")

    try:
        auth_service = await get_auth_service_instance()
        users = await auth_service.list_users(
            tenant_id=tenant_id or current_user.get("tenant_id"),
            limit=limit,
            offset=offset,
        )

        return [
            UserResponse(
                user_id=user.user_id,
                email=user.email,
                full_name=getattr(user, 'full_name', None),
                tenant_id=user.tenant_id,
                roles=user.roles,
                preferences=getattr(user, 'preferences', {}),
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat(),
            )
            for user in users
        ]

    except AuthError as e:
        http_error(400, ErrorCode.SERVICE_ERROR, str(e))
    except Exception:
        http_error(500, ErrorCode.INTERNAL_ERROR, "Failed to list users")
