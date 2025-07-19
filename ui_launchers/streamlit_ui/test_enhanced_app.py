"""
Test script for the enhanced Streamlit UI
Run this to test the premium features and components
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all enhanced components can be imported."""
    print("Testing enhanced UI component imports...")
    
    try:
        from components.premium_theme import PremiumThemeManager
        print("✅ PremiumThemeManager imported successfully")
        
        from components.navigation import EnhancedNavigation
        print("✅ EnhancedNavigation imported successfully")
        
        from components.notifications import NotificationSystem
        print("✅ NotificationSystem imported successfully")
        
        from components.status_bar import StatusBar
        print("✅ StatusBar imported successfully")
        
        from config.premium_routing import PREMIUM_PAGE_MAP, get_user_pages
        print("✅ Premium routing imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_theme_manager():
    """Test the premium theme manager."""
    print("\nTesting PremiumThemeManager...")
    
    try:
        from components.premium_theme import PremiumThemeManager
        
        theme_manager = PremiumThemeManager()
        
        # Test theme loading
        themes = theme_manager.themes
        print(f"✅ Loaded {len(themes)} themes: {list(themes.keys())}")
        
        # Test CSS generation
        css = theme_manager.generate_theme_css('executive')
        assert len(css) > 100, "CSS should be substantial"
        print("✅ CSS generation working")
        
        # Test theme info
        info = theme_manager.get_theme_info('executive')
        assert 'name' in info, "Theme info should contain name"
        print("✅ Theme info retrieval working")
        
        return True
        
    except Exception as e:
        print(f"❌ Theme manager error: {e}")
        return False

def test_navigation():
    """Test the enhanced navigation system."""
    print("\nTesting EnhancedNavigation...")
    
    try:
        from components.navigation import EnhancedNavigation
        
        nav = EnhancedNavigation()
        
        # Test navigation items
        items = nav.navigation_items
        print(f"✅ Loaded {len(items)} navigation items")
        
        # Test categories
        categories = nav.categories
        print(f"✅ Loaded {len(categories)} categories")
        
        # Test user access (mock user context)
        mock_user_ctx = {
            'roles': ['admin'],
            'permissions': ['dashboard.view', 'chat.access']
        }
        
        accessible_items = nav.get_accessible_items(mock_user_ctx)
        print(f"✅ Admin user has access to {len(accessible_items)} pages")
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation error: {e}")
        return False

def test_notifications():
    """Test the notification system."""
    print("\nTesting NotificationSystem...")
    
    try:
        from components.notifications import NotificationSystem, NotificationType, NotificationPriority
        
        notif_system = NotificationSystem()
        
        # Test notification creation
        notif_id = notif_system.add_notification(
            title="Test Notification",
            message="This is a test notification",
            type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL
        )
        
        print("✅ Notification creation working")
        
        # Test notification types
        types = list(NotificationType)
        print(f"✅ {len(types)} notification types available")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification system error: {e}")
        return False

def test_routing():
    """Test the premium routing system."""
    print("\nTesting Premium Routing...")
    
    try:
        from config.premium_routing import PREMIUM_PAGES, get_user_pages, get_default_page
        
        print(f"✅ Loaded {len(PREMIUM_PAGES)} premium pages")
        
        # Test user page access
        mock_user_ctx = {
            'roles': ['admin'],
            'permissions': []
        }
        
        accessible_pages = get_user_pages(mock_user_ctx)
        print(f"✅ Admin user has access to {len(accessible_pages)} pages")
        
        # Test default page
        default_page = get_default_page(mock_user_ctx)
        print(f"✅ Default page for admin: {default_page}")
        
        return True
        
    except Exception as e:
        print(f"❌ Routing error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing AI Karen Enhanced Streamlit UI Components")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_theme_manager,
        test_navigation,
        test_notifications,
        test_routing
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced UI components are ready.")
        print("\nTo run the enhanced UI:")
        print("streamlit run app_enhanced.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())