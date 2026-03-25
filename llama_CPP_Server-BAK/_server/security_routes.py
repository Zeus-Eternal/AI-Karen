"""
Security Routes for Llama.cpp Server

This module provides FastAPI routes for security-related operations including:
- User authentication and management
- API key management
- Security configuration
- Security status monitoring
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Security, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from .security_manager import (
    SecurityManager, 
    User, 
    UserRole, 
    Permission, 
    LoginRequest, 
    LoginResponse, 
    RefreshTokenRequest,
    ChangePasswordRequest,
    CreateAPIKeyRequest,
    APIKeyResponse
)

# Create router for security routes
router = APIRouter(prefix="/auth", tags=["security"])

# Initialize security manager
security_manager = SecurityManager()

# Request models
class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    role: UserRole = Field(default=UserRole.USER)
    permissions: List[Permission] = Field(default_factory=list)

class UpdateUserRequest(BaseModel):
    """Request model for updating a user"""
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None
    permissions: Optional[List[Permission]] = None
    active: Optional[bool] = None

class SecurityConfigRequest(BaseModel):
    """Request model for updating security configuration"""
    secret_key: Optional[str] = Field(None, min_length=16)
    jwt_algorithm: Optional[str] = Field("HS256")
    jwt_expiration: Optional[int] = Field(3600, gt=0)
    password_min_length: Optional[int] = Field(12, gt=0)
    max_login_attempts: Optional[int] = Field(5, gt=0)
    login_lockout_duration: Optional[int] = Field(300, gt=0)
    rate_limit_requests: Optional[int] = Field(100, gt=0)
    rate_limit_window: Optional[int] = Field(60, gt=0)
    enable_api_keys: Optional[bool] = True
    enable_jwt: Optional[bool] = True
    enable_rate_limiting: Optional[bool] = True
    enable_ip_whitelist: Optional[bool] = False
    ip_whitelist: Optional[List[str]] = Field(default_factory=list)
    enable_ip_blacklist: Optional[bool] = False
    ip_blacklist: Optional[List[str]] = Field(default_factory=list)
    enable_request_logging: Optional[bool] = True

class SecurityStatusResponse(BaseModel):
    """Response model for security status"""
    active_users: int
    total_users: int
    active_api_keys: int
    total_api_keys: int
    locked_accounts: int
    security_features: Dict[str, bool]

# Response models
class UserResponse(BaseModel):
    """Response model for user data"""
    username: str
    role: UserRole
    permissions: List[Permission]
    created_at: str
    last_login: Optional[str]
    login_attempts: int
    locked_until: Optional[str]
    active: bool

class APIKeyListResponse(BaseModel):
    """Response model for API key list"""
    keys: List[APIKeyResponse]

class UserListResponse(BaseModel):
    """Response model for user list"""
    users: List[UserResponse]

# Helper functions
def get_user_response(user: User) -> UserResponse:
    """Convert a User object to a UserResponse"""
    return UserResponse(
        username=user.username,
        role=user.role,
        permissions=user.permissions,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login else None,
        login_attempts=user.login_attempts,
        locked_until=user.locked_until.isoformat() if user.locked_until else None,
        active=user.active
    )

# Routes
@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate a user with username and password
    
    Returns JWT tokens if authentication is successful
    """
    response = security_manager.authenticate_user(request.username, request.password)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log security event
    security_manager.log_security_event(
        "user_login",
        {"username": request.username},
        user=request.username
    )
    
    return response

@router.post("/login-form", response_model=LoginResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user with form data (for OAuth2 compatibility)
    
    Returns JWT tokens if authentication is successful
    """
    response = security_manager.authenticate_user(form_data.username, form_data.password)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log security event
    security_manager.log_security_event(
        "user_login",
        {"username": form_data.username},
        user=form_data.username
    )
    
    return response

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh JWT tokens using a refresh token
    
    Returns new JWT tokens if refresh is successful
    """
    response = security_manager.refresh_tokens(request.refresh_token)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return response

@router.post("/logout")
async def logout(current_user: User = Depends(security_manager.get_current_user)):
    """
    Log out the current user
    
    Revokes the user's refresh tokens
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log security event
    security_manager.log_security_event(
        "user_logout",
        {"username": current_user.username},
        user=current_user.username
    )
    
    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(security_manager.get_current_active_user)
):
    """
    Change the current user's password
    
    Validates the old password and updates to the new password
    """
    # Verify old password
    if not security_manager._verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    
    # Validate new password strength
    is_valid, issues = security_manager.validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password is weak: {', '.join(issues)}"
        )
    
    # Update password
    success = security_manager.update_user(
        current_user.username,
        password=request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    # Log security event
    security_manager.log_security_event(
        "password_changed",
        {"username": current_user.username},
        user=current_user.username
    )
    
    return {"message": "Password changed successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(security_manager.get_current_active_user)):
    """
    Get information about the current authenticated user
    """
    return get_user_response(current_user)

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(security_manager.require_permission(Permission.USER_MANAGE))
):
    """
    Create a new user
    
    Requires USER_MANAGE permission
    """
    success = security_manager.create_user(
        request.username,
        request.password,
        request.role,
        request.permissions
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    
    # Log security event
    security_manager.log_security_event(
        "user_created",
        {
            "username": request.username,
            "role": request.role.value,
            "permissions": [p.value for p in request.permissions]
        },
        user=current_user.username
    )
    
    return get_user_response(security_manager.users[request.username])

@router.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: User = Depends(security_manager.require_permission(Permission.USER_MANAGE))
):
    """
    List all users
    
    Requires USER_MANAGE permission
    """
    users = [get_user_response(user) for user in security_manager.users.values()]
    return UserListResponse(users=users)

@router.get("/users/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: User = Depends(security_manager.require_permission(Permission.USER_MANAGE))
):
    """
    Get information about a specific user
    
    Requires USER_MANAGE permission
    """
    if username not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return get_user_response(security_manager.users[username])

@router.put("/users/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    request: UpdateUserRequest,
    current_user: User = Depends(security_manager.require_permission(Permission.USER_MANAGE))
):
    """
    Update a user's information
    
    Requires USER_MANAGE permission
    """
    if username not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build update parameters
    update_params = {}
    if request.password is not None:
        update_params["password"] = request.password
    if request.role is not None:
        update_params["role"] = request.role
    if request.permissions is not None:
        update_params["permissions"] = request.permissions
    if request.active is not None:
        update_params["active"] = request.active
    
    # Update user
    success = security_manager.update_user(username, **update_params)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )
    
    # Log security event
    security_manager.log_security_event(
        "user_updated",
        {
            "username": username,
            "updates": {k: v for k, v in update_params.items() if k != "password"}
        },
        user=current_user.username
    )
    
    return get_user_response(security_manager.users[username])

@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(security_manager.require_permission(Permission.USER_MANAGE))
):
    """
    Delete a user
    
    Requires USER_MANAGE permission
    """
    if username not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = security_manager.delete_user(username)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )
    
    # Log security event
    security_manager.log_security_event(
        "user_deleted",
        {"username": username},
        user=current_user.username
    )
    
    return {"message": "User deleted successfully"}

@router.post("/users/{username}/unlock")
async def unlock_user(
    username: str,
    current_user: User = Depends(security_manager.require_permission(Permission.USER_MANAGE))
):
    """
    Unlock a user account
    
    Requires USER_MANAGE permission
    """
    if username not in security_manager.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = security_manager.users[username]
    if not security_manager._is_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is not locked"
        )
    
    security_manager._unlock_account(user)
    
    # Log security event
    security_manager.log_security_event(
        "user_unlocked",
        {"username": username},
        user=current_user.username
    )
    
    return {"message": "User account unlocked successfully"}

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(security_manager.get_current_active_user)
):
    """
    Create a new API key for the current user
    
    Users can only create API keys for themselves unless they have USER_MANAGE permission
    """
    # If user has USER_MANAGE permission, they can create API keys for other users
    if security_manager.check_permission(current_user, Permission.USER_MANAGE):
        # Extract username from request if provided
        username = request.__dict__.get("user", current_user.username)
    else:
        # Regular users can only create API keys for themselves
        username = current_user.username
    
    response = security_manager.create_api_key(
        username,
        request.name,
        request.permissions,
        request.expires_in_days
    )
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key"
        )
    
    # Log security event
    security_manager.log_security_event(
        "api_key_created",
        {
            "name": request.name,
            "permissions": [p.value for p in request.permissions],
            "expires_in_days": request.expires_in_days
        },
        user=current_user.username
    )
    
    return response

@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(security_manager.get_current_active_user)
):
    """
    List API keys for the current user
    
    Users can only see their own API keys unless they have USER_MANAGE permission
    """
    if security_manager.check_permission(current_user, Permission.USER_MANAGE):
        # Admins can see all API keys
        api_keys = [
            APIKeyResponse(
                key=key.key,
                name=key.name,
                permissions=key.permissions,
                created_at=key.created_at,
                expires_at=key.expires_at
            )
            for key in security_manager.api_keys.values()
            if key.active
        ]
    else:
        # Regular users can only see their own API keys
        api_keys = [
            APIKeyResponse(
                key=key.key,
                name=key.name,
                permissions=key.permissions,
                created_at=key.created_at,
                expires_at=key.expires_at
            )
            for key in security_manager.api_keys.values()
            if key.active and key.user == current_user.username
        ]
    
    return APIKeyListResponse(keys=api_keys)

@router.delete("/api-keys/{key}")
async def revoke_api_key(
    key: str,
    current_user: User = Depends(security_manager.get_current_active_user)
):
    """
    Revoke an API key
    
    Users can only revoke their own API keys unless they have USER_MANAGE permission
    """
    if key not in security_manager.api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key = security_manager.api_keys[key]
    
    # Check if user has permission to revoke this API key
    if not security_manager.check_permission(current_user, Permission.USER_MANAGE) and api_key.user != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to revoke this API key"
        )
    
    success = security_manager.revoke_api_key(key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke API key"
        )
    
    # Log security event
    security_manager.log_security_event(
        "api_key_revoked",
        {"name": api_key.name},
        user=current_user.username
    )
    
    return {"message": "API key revoked successfully"}

@router.get("/security/status", response_model=SecurityStatusResponse)
async def get_security_status(
    current_user: User = Depends(security_manager.require_permission(Permission.ADMIN))
):
    """
    Get the current security status
    
    Requires ADMIN permission
    """
    status = security_manager.get_security_status()
    return SecurityStatusResponse(**status)

@router.put("/security/config")
async def update_security_config(
    request: SecurityConfigRequest,
    current_user: User = Depends(security_manager.require_permission(Permission.ADMIN))
):
    """
    Update security configuration
    
    Requires ADMIN permission
    """
    # Update security configuration
    config_updates = request.dict(exclude_unset=True)
    
    for key, value in config_updates.items():
        security_manager.config_manager.set(f"security.{key}", value)
    
    success = security_manager.config_manager.save()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security configuration"
        )
    
    # Log security event
    security_manager.log_security_event(
        "security_config_updated",
        {"updates": list(config_updates.keys())},
        user=current_user.username
    )
    
    return {"message": "Security configuration updated successfully"}

@router.get("/security/config")
async def get_security_config(
    current_user: User = Depends(security_manager.require_permission(Permission.ADMIN))
):
    """
    Get the current security configuration
    
    Requires ADMIN permission
    """
    # Get security configuration
    config = {}
    
    # Get all security-related config values
    for key in [
        "secret_key",
        "jwt_algorithm",
        "jwt_expiration",
        "password_min_length",
        "max_login_attempts",
        "login_lockout_duration",
        "rate_limit_requests",
        "rate_limit_window",
        "enable_api_keys",
        "enable_jwt",
        "enable_rate_limiting",
        "enable_ip_whitelist",
        "ip_whitelist",
        "enable_ip_blacklist",
        "ip_blacklist",
        "enable_request_logging"
    ]:
        config[key] = security_manager.config_manager.get(f"security.{key}")
    
    # Don't expose the actual secret key
    if "secret_key" in config:
        config["secret_key"] = "***REDACTED***"
    
    return config