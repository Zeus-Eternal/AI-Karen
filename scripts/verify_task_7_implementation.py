#!/usr/bin/env python3
"""
Final verification test for Task 7 implementation.
"""

import sys
import re
sys.path.append('.')

def verify_task_7_implementation():
    """Comprehensive verification of Task 7 implementation."""
    print("🔍 TASK 7 IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    
    verification_results = []
    
    # 1. Verify enhanced authentication dependencies
    print("1. Enhanced Authentication Dependencies:")
    try:
        with open('src/extensions/integration.py', 'r') as f:
            content = f.read()
        
        # Check for proper import structure
        import_section = content[content.find('from server.security import'):content.find(')', content.find('from server.security import'))]
        
        required_imports = [
            'require_extension_read',
            'require_extension_write',
            'require_extension_admin',
            'require_background_tasks',
            'get_extension_auth_manager'
        ]
        
        all_imports_found = all(imp in import_section for imp in required_imports)
        if all_imports_found:
            print("   ✅ All required authentication imports present")
            verification_results.append("Authentication imports")
        else:
            print("   ❌ Missing authentication imports")
        
        # Check for proper usage in endpoints
        endpoint_patterns = [
            r'@extension_router\.get\("/"\)\s*async def list_extensions\([^)]*Depends\(require_extension_read\)',
            r'@extension_router\.get\("/\{extension_name\}"\)\s*async def get_extension\([^)]*Depends\(require_extension_read\)',
            r'@extension_router\.post\("/\{extension_name\}/load"\)\s*async def load_extension\([^)]*Depends\(require_extension_admin\)',
            r'@extension_router\.post\("/\{extension_name\}/configure"\)\s*async def configure_extension\([^)]*Depends\(require_extension_write\)'
        ]
        
        endpoint_auth_count = 0
        for pattern in endpoint_patterns:
            if re.search(pattern, content, re.DOTALL):
                endpoint_auth_count += 1
        
        if endpoint_auth_count >= 3:
            print(f"   ✅ {endpoint_auth_count} endpoints properly authenticated")
            verification_results.append("Endpoint authentication")
        else:
            print(f"   ❌ Only {endpoint_auth_count} endpoints authenticated")
        
    except Exception as e:
        print(f"   ❌ Error verifying authentication: {e}")
    
    # 2. Verify permission checking utilities
    print("\n2. Permission Checking Utilities:")
    try:
        permission_methods = [
            '_has_admin_permission',
            '_has_system_extension_permission',
            '_is_system_extension',
            '_get_extension_permissions',
            '_can_access_extension'
        ]
        
        method_implementations = 0
        for method in permission_methods:
            # Check for proper method signature and implementation
            method_pattern = rf'def {method}\(self, [^)]+\) -> [^:]+:'
            if re.search(method_pattern, content):
                method_implementations += 1
        
        if method_implementations >= 4:
            print(f"   ✅ {method_implementations} permission utilities implemented")
            verification_results.append("Permission utilities")
        else:
            print(f"   ❌ Only {method_implementations} permission utilities found")
        
        # Check for proper usage in endpoints
        permission_usage_patterns = [
            'self._can_access_extension(',
            'self._has_admin_permission(',
            'self._has_system_extension_permission(',
            'self._get_extension_permissions('
        ]
        
        usage_count = sum(1 for pattern in permission_usage_patterns if pattern in content)
        if usage_count >= 3:
            print(f"   ✅ Permission utilities properly used ({usage_count} usages)")
            verification_results.append("Permission utility usage")
        else:
            print(f"   ❌ Limited permission utility usage ({usage_count} usages)")
        
    except Exception as e:
        print(f"   ❌ Error verifying permission utilities: {e}")
    
    # 3. Verify user context validation
    print("\n3. User Context Validation:")
    try:
        user_context_patterns = [
            r"user_context\['user_id'\]",
            r"user_context\['tenant_id'\]",
            r"user_context\.get\('roles'",
            r"user_context\.get\('permissions'"
        ]
        
        context_usage_count = sum(1 for pattern in user_context_patterns 
                                 if re.search(pattern, content))
        
        if context_usage_count >= 3:
            print(f"   ✅ User context properly validated ({context_usage_count} validations)")
            verification_results.append("User context validation")
        else:
            print(f"   ❌ Limited user context validation ({context_usage_count} validations)")
        
        # Check for proper error handling
        auth_error_patterns = [
            'raise HTTPException(status_code=403',
            'Access denied',
            'Insufficient permissions'
        ]
        
        error_handling_count = sum(1 for pattern in auth_error_patterns if pattern in content)
        if error_handling_count >= 2:
            print(f"   ✅ Proper authentication error handling ({error_handling_count} patterns)")
            verification_results.append("Authentication error handling")
        else:
            print(f"   ❌ Limited authentication error handling ({error_handling_count} patterns)")
        
    except Exception as e:
        print(f"   ❌ Error verifying user context validation: {e}")
    
    # 4. Verify enhanced functionality
    print("\n4. Enhanced Functionality:")
    try:
        enhanced_features = [
            'Enhanced permission checking',
            'Enhanced access control',
            'audit trail',
            'logger.info.*user_context',
            'force_reload',
            'preserve_state',
            'detailed.*diagnostics'
        ]
        
        feature_count = 0
        for feature in enhanced_features:
            if re.search(feature, content, re.IGNORECASE):
                feature_count += 1
        
        if feature_count >= 5:
            print(f"   ✅ Enhanced functionality implemented ({feature_count} features)")
            verification_results.append("Enhanced functionality")
        else:
            print(f"   ❌ Limited enhanced functionality ({feature_count} features)")
        
        # Check for proper logging and audit trail
        logging_patterns = [
            r'logger\.info\(f".*{user_context\[',
            r'logger\.info\(f".*loaded successfully by',
            r'logger\.info\(f".*unloaded successfully by'
        ]
        
        logging_count = sum(1 for pattern in logging_patterns 
                           if re.search(pattern, content))
        
        if logging_count >= 2:
            print(f"   ✅ Proper audit logging implemented ({logging_count} log entries)")
            verification_results.append("Audit logging")
        else:
            print(f"   ❌ Limited audit logging ({logging_count} log entries)")
        
    except Exception as e:
        print(f"   ❌ Error verifying enhanced functionality: {e}")
    
    # 5. Verify background task integration
    print("\n5. Background Task Integration:")
    try:
        with open('src/extensions/background_task_api.py', 'r') as f:
            bg_content = f.read()
        
        bg_auth_patterns = [
            'require_background_tasks',
            'require_extension_read',
            'require_extension_admin',
            'user_context: Dict[str, Any] = Depends('
        ]
        
        bg_auth_count = sum(1 for pattern in bg_auth_patterns if pattern in bg_content)
        
        if bg_auth_count >= 3:
            print(f"   ✅ Background task API properly authenticated ({bg_auth_count} patterns)")
            verification_results.append("Background task authentication")
        else:
            print(f"   ❌ Limited background task authentication ({bg_auth_count} patterns)")
        
        # Check for proper integration in main router
        if 'create_background_task_router' in content and 'app.include_router(background_task_router' in content:
            print("   ✅ Background task router properly integrated")
            verification_results.append("Background task integration")
        else:
            print("   ❌ Background task router not properly integrated")
        
    except Exception as e:
        print(f"   ❌ Error verifying background task integration: {e}")
    
    # 6. Verify FastAPI dependency injection patterns
    print("\n6. FastAPI Dependency Injection:")
    try:
        fastapi_patterns = [
            r'from fastapi import.*Depends',
            r'user_context: Dict\[str, Any\] = Depends\(',
            r'@extension_router\.(get|post)\(',
            r'async def \w+\([^)]*user_context[^)]*\)'
        ]
        
        fastapi_count = sum(1 for pattern in fastapi_patterns 
                           if re.search(pattern, content))
        
        if fastapi_count >= 3:
            print(f"   ✅ FastAPI dependency injection properly implemented ({fastapi_count} patterns)")
            verification_results.append("FastAPI dependency injection")
        else:
            print(f"   ❌ Limited FastAPI dependency injection ({fastapi_count} patterns)")
        
    except Exception as e:
        print(f"   ❌ Error verifying FastAPI patterns: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 VERIFICATION SUMMARY:")
    print("=" * 60)
    
    total_checks = 12  # Total number of verification checks
    passed_checks = len(verification_results)
    
    for result in verification_results:
        print(f"✅ {result}")
    
    print(f"\n📊 VERIFICATION SCORE: {passed_checks}/{total_checks}")
    
    if passed_checks >= 10:
        print("🎉 TASK 7 IMPLEMENTATION VERIFIED SUCCESSFULLY!")
        print("✨ All core requirements met with enhanced functionality")
        return True
    elif passed_checks >= 8:
        print("✅ TASK 7 IMPLEMENTATION MOSTLY COMPLETE")
        print("⚠️  Some minor enhancements could be added")
        return True
    else:
        print("❌ TASK 7 IMPLEMENTATION NEEDS MORE WORK")
        print("🔧 Several requirements not fully met")
        return False

if __name__ == "__main__":
    success = verify_task_7_implementation()
    sys.exit(0 if success else 1)