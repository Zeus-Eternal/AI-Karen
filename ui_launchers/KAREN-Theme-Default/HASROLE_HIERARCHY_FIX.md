# hasRole Hierarchy Fix

## Problem

The `hasRole` function in `AuthContext.tsx` was using **exact role matching** instead of **role hierarchy**. This caused permission issues after successful login, where admins couldn't access user-level features.

### Example of the Bug
- User logs in as `admin`
- System checks if user has `user` role
- **Before fix**: `"admin" === "user"` → ❌ false (access denied)
- **After fix**: `ROLE_HIERARCHY["admin"] >= ROLE_HIERARCHY["user"]` → ✅ true (access granted)

## Root Cause

In `src/contexts/AuthContext.tsx:608-621`, the hasRole function was implemented as:

```typescript
const hasRole = useCallback(
  (role: UserRole): boolean => {
    if (!user) return false;

    if (user.role) {
      return user.role === role;  // ❌ EXACT MATCH BUG
    }

    return user.roles.includes(role);  // ❌ EXACT MATCH BUG
  },
  [user]
);
```

This meant that:
- Super admins couldn't access admin features
- Admins couldn't access user features
- Role hierarchy was completely ignored

## Solution

Updated `hasRole` to use the `ROLE_HIERARCHY` constant from `rbac-shared.ts`:

```typescript
const hasRole = useCallback(
  (role: UserRole): boolean => {
    if (!user) return false;

    // Get user's highest role
    const userRole = user.role || getHighestRole(user.roles);

    // Use role hierarchy instead of exact matching
    const userRoleLevel = ROLE_HIERARCHY[userRole] ?? 0;
    const requiredRoleLevel = ROLE_HIERARCHY[role] ?? 0;

    return userRoleLevel >= requiredRoleLevel;
  },
  [user]
);
```

### Role Hierarchy
```typescript
ROLE_HIERARCHY = {
  user: 1,
  admin: 2,
  super_admin: 3
}
```

Now:
- `super_admin` (level 3) can access `admin` (level 2) and `user` (level 1) features ✅
- `admin` (level 2) can access `user` (level 1) features ✅
- `user` (level 1) can only access `user` (level 1) features ✅

## Files Changed

### Core Fix
- **`src/contexts/AuthContext.tsx`**
  - Imported `ROLE_HIERARCHY` from `rbac-shared.ts`
  - Updated `hasRole` function to use hierarchy comparison (lines 608-623)
  - Simplified `isAdmin` function (removed redundant OR check)

### Simplified Redundant Checks
With hierarchy in place, `hasRole("admin") || hasRole("super_admin")` became redundant since super_admins automatically pass `hasRole("admin")`. Simplified in:

- **`src/components/navigation/AdminBreadcrumbs.tsx`** (line 76)
- **`src/components/admin/UserActivityMonitor.tsx`** (line 80)

## Impact

### Before Fix
1. User logs in successfully as admin
2. ProtectedRoute checks if user has "user" role
3. hasRole("user") returns false for admin user
4. User redirected to `/unauthorized` or `/login`
5. **Result**: Login success but immediate redirect (permission loop)

### After Fix
1. User logs in successfully as admin
2. ProtectedRoute checks if user has "user" role
3. hasRole("user") returns true (admin level 2 >= user level 1)
4. User stays on intended page
5. **Result**: Login success and proper access ✅

## Testing Recommendations

1. **Admin Login Flow**
   - Login as admin
   - Verify redirect to intended page (not /unauthorized)
   - Verify access to user-level features

2. **Super Admin Login Flow**
   - Login as super_admin
   - Verify access to admin features
   - Verify access to user features

3. **User Login Flow**
   - Login as user
   - Verify access to user features
   - Verify NO access to admin features

4. **Role Checks**
   - Verify `hasRole("user")` returns true for all roles
   - Verify `hasRole("admin")` returns true for admin and super_admin
   - Verify `hasRole("super_admin")` returns true only for super_admin

## Related Files

The fix automatically propagates to all components using `hasRole` from AuthContext:
- `ProtectedRoute.tsx` - Main route protection
- `AdminRoute.tsx` - Admin route wrapper
- `SuperAdminRoute.tsx` - Super admin route wrapper
- `RoleBasedNavigation.tsx` - Navigation visibility
- `EnhancedBulkUserOperations.tsx` - Operation filtering
- All other components using `useAuth().hasRole()`

## References

- **Role Hierarchy Definition**: `src/components/security/rbac-shared.ts`
- **Correct Implementation Reference**: `src/components/security/usePermissions.ts` (already had correct hierarchy implementation)
- **Related Documentation**: `LOGIN_AUDIT_REPORT.md`, `LOGIN_REDIRECT_FIX.md`
