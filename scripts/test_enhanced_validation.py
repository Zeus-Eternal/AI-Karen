#!/usr/bin/env python3
"""
Test Enhanced Authentication Validation

This script tests the new enhanced authentication validation features
to ensure they work correctly with the updated database schema.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_form_validation():
    """Test the enhanced form validation features."""
    logger.info("Testing enhanced form validation...")
    
    try:
        from src.ai_karen_engine.guardrails.validator import (
            validate_login_form,
            validate_registration_form,
            validate_password_strength,
            get_password_strength_score,
            ValidationError
        )
        
        # Test login form validation
        logger.info("Testing login form validation...")
        
        # Valid login with email
        try:
            validate_login_form({
                "email": "test@example.com",
                "password": "testpassword123"
            })
            logger.info("✅ Valid email login passed")
        except ValidationError as e:
            logger.error(f"❌ Valid email login failed: {e}")
        
        # Valid login with username
        try:
            validate_login_form({
                "username": "testuser",
                "password": "testpassword123"
            })
            logger.info("✅ Valid username login passed")
        except ValidationError as e:
            logger.error(f"❌ Valid username login failed: {e}")
        
        # Invalid login (no identifier)
        try:
            validate_login_form({
                "password": "testpassword123"
            })
            logger.error("❌ Invalid login should have failed")
        except ValidationError:
            logger.info("✅ Invalid login correctly rejected")
        
        # Test registration form validation
        logger.info("Testing registration form validation...")
        
        # Valid registration
        try:
            validate_registration_form({
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!"
            })
            logger.info("✅ Valid registration passed")
        except ValidationError as e:
            logger.error(f"❌ Valid registration failed: {e}")
        
        # Invalid registration (weak password)
        try:
            validate_registration_form({
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "weak",
                "confirm_password": "weak"
            })
            logger.error("❌ Weak password should have failed")
        except ValidationError:
            logger.info("✅ Weak password correctly rejected")
        
        # Test password strength validation
        logger.info("Testing password strength validation...")
        
        # Strong password
        strong_checks = validate_password_strength("StrongPass123!")
        strong_score = get_password_strength_score("StrongPass123!")
        logger.info(f"Strong password checks: {strong_checks}")
        logger.info(f"Strong password score: {strong_score}")
        
        # Weak password
        weak_checks = validate_password_strength("weak")
        weak_score = get_password_strength_score("weak")
        logger.info(f"Weak password checks: {weak_checks}")
        logger.info(f"Weak password score: {weak_score}")
        
        logger.info("✅ Form validation tests completed")
        
    except ImportError as e:
        logger.error(f"❌ Could not import validation modules: {e}")
    except Exception as e:
        logger.error(f"❌ Form validation test failed: {e}")


async def test_auth_service():
    """Test the enhanced authentication service."""
    logger.info("Testing enhanced authentication service...")
    
    try:
        from src.ai_karen_engine.services.production_auth_service import ProductionAuthService
        from src.ai_karen_engine.core.services.base import ServiceConfig
        
        # Initialize service
        config = ServiceConfig(
            name="test_auth",
            enabled=True,
            config={
                "users_file": "data/test_users.json",
                "require_strong_passwords": True,
                "enable_audit_logging": True
            }
        )
        
        auth_service = ProductionAuthService(config)
        await auth_service.initialize()
        
        # Test health check
        is_healthy = await auth_service.health_check()
        if is_healthy:
            logger.info("✅ Authentication service health check passed")
        else:
            logger.error("❌ Authentication service health check failed")
        
        # Test first-run check
        is_first_run = await auth_service.is_first_run()
        logger.info(f"First run status: {is_first_run}")
        
        # Test user creation with validation
        if is_first_run:
            try:
                user = await auth_service.create_first_admin(
                    email="admin@test.local",
                    password="AdminPass123!",
                    full_name="Test Administrator"
                )
                logger.info(f"✅ Created first admin user: {user.email}")
            except Exception as e:
                logger.error(f"❌ Failed to create first admin: {e}")
        
        # Test authentication
        try:
            user, access_token, refresh_token = await auth_service.authenticate_user(
                email="admin@test.local",
                password="AdminPass123!",
                ip_address="127.0.0.1",
                user_agent="test-client"
            )
            
            if user and access_token:
                logger.info(f"✅ Authentication successful for: {user.email}")
            else:
                logger.error(f"❌ Authentication failed: {refresh_token}")
        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
        
        # Test authentication statistics
        try:
            stats = await auth_service.get_auth_stats()
            logger.info(f"Authentication statistics: {stats}")
            logger.info("✅ Statistics retrieval successful")
        except Exception as e:
            logger.error(f"❌ Statistics retrieval failed: {e}")
        
        await auth_service.stop()
        logger.info("✅ Authentication service tests completed")
        
    except ImportError as e:
        logger.error(f"❌ Could not import authentication service: {e}")
    except Exception as e:
        logger.error(f"❌ Authentication service test failed: {e}")


async def test_database_functions():
    """Test the new database functions."""
    logger.info("Testing database functions...")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Get database connection
        db_url = os.getenv('DATABASE_URL', 'postgresql://karen_user:karen_password@localhost:5432/ai_karen')
        
        conn = psycopg2.connect(db_url)
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Test password strength validation function
            cursor.execute("""
                SELECT * FROM validate_password_strength('StrongPass123!', 'testuser')
            """)
            result = cursor.fetchone()
            logger.info(f"Password strength validation result: {result}")
            
            # Test rate limiting function
            cursor.execute("""
                SELECT * FROM check_rate_limit('127.0.0.1', 'ip', 10, 15)
            """)
            result = cursor.fetchone()
            logger.info(f"Rate limit check result: {result}")
            
            # Test security event logging
            cursor.execute("""
                SELECT log_security_event(
                    'TEST_EVENT',
                    'info',
                    NULL,
                    'test@example.com',
                    'testuser',
                    '127.0.0.1'::inet,
                    'test-client',
                    true,
                    NULL,
                    NULL,
                    '{"test": true}'::jsonb
                )
            """)
            event_id = cursor.fetchone()[0]
            logger.info(f"Security event logged with ID: {event_id}")
            
            # Test enhanced statistics view
            cursor.execute("SELECT * FROM auth_statistics_enhanced")
            stats = cursor.fetchone()
            logger.info(f"Enhanced statistics: {dict(stats)}")
            
            conn.commit()
            logger.info("✅ Database function tests completed")
        
        conn.close()
        
    except ImportError:
        logger.error("❌ psycopg2 not available, skipping database tests")
    except Exception as e:
        logger.error(f"❌ Database function test failed: {e}")


async def main():
    """Main test function."""
    logger.info("Enhanced Authentication Validation Test Suite")
    logger.info("=" * 60)
    
    # Run all tests
    await test_form_validation()
    print()
    
    await test_auth_service()
    print()
    
    await test_database_functions()
    print()
    
    logger.info("=" * 60)
    logger.info("Test suite completed!")
    logger.info("\nIf all tests passed, your enhanced authentication system is ready!")
    logger.info("\nNext steps:")
    logger.info("1. Deploy the updated authentication service")
    logger.info("2. Update your frontend to use the new validation features")
    logger.info("3. Monitor the auth_statistics_enhanced view for metrics")
    logger.info("4. Configure password policies as needed")


if __name__ == "__main__":
    asyncio.run(main())