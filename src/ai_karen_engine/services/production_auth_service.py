"""
Production Authentication Service

This module re-exports the AuthService and UserAccount classes from the auth_service module
for backward compatibility with existing code.
"""

from ai_karen_engine.services.auth_service import AuthService, UserAccount

__all__ = [
    "AuthService",
    "UserAccount",
]