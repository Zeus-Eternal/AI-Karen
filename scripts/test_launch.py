#!/usr/bin/env python3
"""
Test script for extension ecosystem launch.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_launch_system():
    """Test the launch system components."""
    print("🧪 Testing Kari Extensions Ecosystem Launch System")
    print()
    
    try:
        # Test launch manager import
        from core.extensions.launch.launch_manager import LaunchManager
        print("✅ LaunchManager imported successfully")
        
        # Test SDK import
        from core.extensions.sdk.extension_sdk import ExtensionSDK
        print("✅ ExtensionSDK imported successfully")
        
        # Test onboarding import
        from core.extensions.onboarding.onboarding_manager import OnboardingManager
        print("✅ OnboardingManager imported successfully")
        
        # Test community import
        from core.extensions.community.community_manager import CommunityManager
        print("✅ CommunityManager imported successfully")
        
        print()
        print("🎉 All core components loaded successfully!")
        print()
        
        # Test launch configuration
        launch_manager = LaunchManager()
        print("📋 Launch Configuration:")
        print(f"  • Launch phases: {len(launch_manager.launch_config['launch_phases'])}")
        print(f"  • Initial extensions: {len(launch_manager.launch_config['initial_extensions'])}")
        print(f"  • Checklist items: {len(launch_manager.launch_config['launch_checklist'])}")
        
        print()
        print("🚀 Extension Ecosystem Launch System Ready!")
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install watchdog jsonschema requests")
        print("2. Execute launch: python scripts/kari-ext-launch execute --phase beta")
        print("3. Check status: python scripts/kari-ext-launch status")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = test_launch_system()
    sys.exit(0 if success else 1)