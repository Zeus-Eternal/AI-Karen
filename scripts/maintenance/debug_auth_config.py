#!/usr/bin/env python3
"""
Debug auth configuration to see what's being loaded
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Set minimal environment variables
os.environ.setdefault('KARI_DUCKDB_PASSWORD', 'dev-duckdb-pass')
os.environ.setdefault('KARI_JOB_ENC_KEY', 'MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo=')
os.environ.setdefault('KARI_JOB_SIGNING_KEY', 'dev-job-key-456')

def debug_auth_config():
    """Debug auth configuration"""
    
    try:
        from ai_karen_engine.auth.config import AuthConfig
        
        print("Loading auth configuration...")
        config = AuthConfig.load()
        
        print(f"Database URL: {config.database.database_url}")
        print(f"Use Database: {config.features.use_database}")
        print(f"Enable Rate Limiting: {config.features.enable_rate_limiting}")
        print(f"Enable Security Features: {config.features.enable_security_features}")
        
        # Check environment variables
        print("\nEnvironment variables:")
        env_vars = [
            'AUTH_DATABASE_URL',
            'POSTGRES_URL', 
            'DATABASE_URL',
            'AUTH_ENABLE_RATE_LIMITING',
            'AUTH_SECRET_KEY'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if 'password' in var.lower() or 'secret' in var.lower() or 'key' in var.lower():
                    value = value[:10] + "..." if len(value) > 10 else "***"
                print(f"  {var}: {value}")
            else:
                print(f"  {var}: (not set)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_auth_config()
    if success:
        print("\n✅ Config debug completed")
    else:
        print("\n❌ Config debug failed")