#!/usr/bin/env python3
"""
Diagnostic script to identify the root causes of:
1. "Skipping fallback scan during static export" 
2. "Backend unavailable, using defaults: Backend responded with 401"
"""

import os
import sys
import requests
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_static_export_configuration():
    """Check Next.js static export configuration"""
    logger.info("=== Checking Static Export Configuration ===")
    
    next_config_path = Path("ui_launchers/KAREN-Theme-Default/next.config.js")
    if not next_config_path.exists():
        logger.error("❌ next.config.js not found")
        return False
    
    with open(next_config_path, 'r') as f:
        config_content = f.read()
    
    # Check if static export is enabled
    if "output: 'export'" in config_content:
        logger.info("✅ Static export is enabled")
    else:
        logger.warning("⚠️  Static export is commented out/disabled")
        logger.info("   Found: // output: 'export',")
    
    # Check for fallback scan configuration
    if "fallback" in config_content.lower():
        logger.info("✅ Fallback configuration found")
    else:
        logger.warning("⚠️  No fallback configuration found")
    
    return True

def check_backend_authentication():
    """Check backend authentication configuration"""
    logger.info("=== Checking Backend Authentication ===")
    
    # Check environment variables
    env_vars = [
        'AUTH_SECRET_KEY',
        'KAREN_BACKEND_URL', 
        'NEXT_PUBLIC_KAREN_BACKEND_URL',
        'AUTH_DEV_MODE',
        'AUTH_ENABLE_SECURITY_FEATURES'
    ]
    
    missing_vars = []
    for var in env_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'***' if 'SECRET' in var or 'KEY' in var else value}")
        else:
            logger.warning(f"⚠️  {var}: not set")
            missing_vars.append(var)
    
    # Check backend connectivity
    backend_url = os.getenv('KAREN_BACKEND_URL', 'http://localhost:8000')
    health_url = f"{backend_url}/health"
    
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Backend health check passed: {health_url}")
            return True
        elif response.status_code == 401:
            logger.error(f"❌ Backend returned 401: {health_url}")
            logger.info("   This indicates authentication is required but not properly configured")
            return False
        else:
            logger.warning(f"⚠️  Backend returned {response.status_code}: {health_url}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Cannot connect to backend: {health_url}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"❌ Backend connection timeout: {health_url}")
        return False
    except Exception as e:
        logger.error(f"❌ Backend connection error: {e}")
        return False

def check_extension_auth_config():
    """Check extension authentication configuration"""
    logger.info("=== Checking Extension Authentication ===")
    
    try:
        # Try to import and check extension auth
        sys.path.insert(0, 'server')
        from security import get_extension_auth_manager
        from config import settings
        
        auth_manager = get_extension_auth_manager()
        logger.info("✅ Extension auth manager initialized")
        
        # Check auth configuration
        auth_config = settings.get_extension_auth_config()
        logger.info(f"✅ Auth mode: {auth_config.get('auth_mode', 'unknown')}")
        logger.info(f"✅ Auth enabled: {auth_config.get('enabled', 'unknown')}")
        logger.info(f"✅ Dev bypass: {auth_config.get('dev_bypass_enabled', 'unknown')}")
        
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️  Cannot import extension auth: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Extension auth check failed: {e}")
        return False

def check_database_connectivity():
    """Check database connectivity"""
    logger.info("=== Checking Database Connectivity ===")
    
    db_url = os.getenv('AUTH_DATABASE_URL')
    if not db_url:
        logger.warning("⚠️  AUTH_DATABASE_URL not set")
        return False
    
    # Mask password in logs
    masked_url = db_url.split('@')[-1] if '@' in db_url else '***'
    logger.info(f"📊 Database URL: ...@{masked_url}")
    
    try:
        # Try to connect to database
        import asyncpg
        import asyncio
        
        async def test_connection():
            try:
                conn = await asyncpg.connect(db_url)
                await conn.close()
                logger.info("✅ Database connection successful")
                return True
            except Exception as e:
                logger.error(f"❌ Database connection failed: {e}")
                return False
        
        return asyncio.run(test_connection())
        
    except ImportError:
        logger.warning("⚠️  asyncpg not available for database test")
        return False
    except Exception as e:
        logger.error(f"❌ Database test error: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    logger.info("🔍 Starting AI Karen Diagnostic")
    logger.info(f"📅 Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 50)
    
    results = {
        'static_export': check_static_export_configuration(),
        'backend_auth': check_backend_authentication(),
        'extension_auth': check_extension_auth_config(),
        'database': check_database_connectivity()
    }
    
    logger.info("=" * 50)
    logger.info("📋 DIAGNOSTIC SUMMARY")
    logger.info("=" * 50)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{check}: {status}")
    
    # Identify likely root causes
    logger.info("=" * 50)
    logger.info("🎯 LIKELY ROOT CAUSES")
    logger.info("=" * 50)
    
    if not results['backend_auth']:
        logger.info("1. Backend 401 Error:")
        logger.info("   - Authentication system is not properly configured")
        logger.info("   - AUTH_SECRET_KEY may be missing or incorrect")
        logger.info("   - Backend may be running in production mode with dev settings")
    
    if not results['static_export']:
        logger.info("2. Static Export Issue:")
        logger.info("   - Static export is disabled in next.config.js")
        logger.info("   - Fallback scan is being skipped due to configuration")
    
    if not results['extension_auth']:
        logger.info("3. Extension Auth Issue:")
        logger.info("   - Extension authentication system not initialized")
        logger.info("   - May be causing 401 errors for extension APIs")
    
    if not results['database']:
        logger.info("4. Database Connectivity Issue:")
        logger.info("   - Database connection is failing")
        logger.info("   - May be causing authentication failures")
    
    logger.info("=" * 50)
    logger.info("🔧 RECOMMENDED FIXES")
    logger.info("=" * 50)
    
    if not results['backend_auth']:
        logger.info("For Backend 401 Error:")
        logger.info("1. Check AUTH_SECRET_KEY environment variable")
        logger.info("2. Verify backend is running with correct configuration")
        logger.info("3. Check if authentication middleware is properly configured")
    
    if not results['static_export']:
        logger.info("For Static Export:")
        logger.info("1. Uncomment 'output: export' in next.config.js")
        logger.info("2. Ensure static export is compatible with your deployment")
    
    return results

if __name__ == "__main__":
    main()