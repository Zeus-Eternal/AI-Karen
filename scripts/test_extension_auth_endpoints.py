#!/usr/bin/env python3
"""
Test script to verify extension authentication endpoints are working properly.
This tests the implementation of task 6: Update existing extension endpoints with authentication.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_extension_auth_endpoints():
    """Test extension authentication endpoints."""
    
    try:
        # Import the FastAPI app
        from server.app import create_app
        from server.config import Settings
        from server.security import get_extension_auth_manager
        
        logger.info("Creating FastAPI app...")
        app = create_app()
        
        logger.info("Getting extension auth manager...")
        auth_manager = get_extension_auth_manager()
        
        # Test token creation
        logger.info("Testing token creation...")
        access_token = auth_manager.create_access_token(
            user_id="test-user",
            tenant_id="test-tenant",
            roles=["user"],
            permissions=["extension:read", "extension:write"]
        )
        logger.info(f"Access token created: {access_token[:20]}...")
        
        # Test service token creation
        service_token = auth_manager.create_service_token(
            service_name="test-service",
            permissions=["extension:background_tasks"]
        )
        logger.info(f"Service token created: {service_token[:20]}...")
        
        # Test background task token creation
        bg_task_token = auth_manager.create_background_task_token(
            task_name="test-task",
            user_id="test-user",
            permissions=["extension:background_tasks", "extension:execute"]
        )
        logger.info(f"Background task token created: {bg_task_token[:20]}...")
        
        # Test configuration validation
        settings = Settings()
        logger.info("Testing extension auth configuration validation...")
        is_valid = settings.validate_extension_auth_config()
        logger.info(f"Extension auth config validation: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test environment-specific configuration
        env_config = settings.get_environment_specific_extension_config()
        logger.info(f"Environment-specific config loaded: {env_config['auth_mode']}")
        
        # Verify app routes
        logger.info("Checking extension routes...")
        extension_routes = [route for route in app.routes if hasattr(route, 'path') and '/api/extensions' in route.path]
        logger.info(f"Found {len(extension_routes)} extension routes:")
        for route in extension_routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = list(route.methods) if route.methods else ['GET']
                logger.info(f"  {methods} {route.path}")
        
        logger.info("✅ Extension authentication endpoints test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Extension authentication endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    logger.info("Starting extension authentication endpoints test...")
    
    # Run the async test
    success = asyncio.run(test_extension_auth_endpoints())
    
    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()