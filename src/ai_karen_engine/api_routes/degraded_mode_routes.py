"""
Degraded Mode Routes — Retired.

Degraded mode management is now handled by:
  - ChatRuntimeControlPlane (core/chat_runtime_control_plane.py)
  - Runtime Admin Routes (api_routes/runtime_admin_routes.py)

This module exists only to prevent import errors during auto-discovery.
No routes are registered.
"""

# No router — prevents auto-discovery from mounting stale endpoints.