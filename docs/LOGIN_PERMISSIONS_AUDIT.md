# Login & Post-Login Permissions Audit Report

**Date:** 2025-11-15
**Issue:** Successful login redirects/exits due to privilege issues
**Status:** ✅ Audit Complete

## Executive Summary

After auditing the login flow and permission system, we've identified that the system is **overly complicated** with unnecessary complexity that can cause user experience issues. The "redirect on login" issue is caused by aggressive permission checks combined with an overly granular RBAC system.

---

## 1. Login Flow Analysis

### Current Flow

```
1. User submits credentials → LoginForm.tsx
2. AuthContext.login() → POST /api/auth/login
3. Session established → setUser(), setIsAuthenticated(true)
4. LoginPageClient redirects to:
   - Query param: ?redirectPath=/some/path
   - SessionStorage: redirectAfterLogin
   - Default: / (home page)
5. ProtectedRoute checks permissions
6. If insufficient permissions → redirect to /unauthorized
```

**Files Involved:**
- `src/components/auth/LoginForm.tsx` (lines 147-172)
- `src/contexts/AuthContext.tsx` (lines 412-588)
- `src/app/login/LoginPageClient.tsx` (lines 10-22)
- `src/components/auth/ProtectedRoute.tsx` (lines 40-90)

### Issue Identified

The redirect issue occurs because:

1. **User logs in successfully** → redirected to `/` or saved path
2. **10-second grace period** prevents immediate permission checks (ProtectedRoute.tsx:63-65)
3. If user navigates to `/admin` → **SuperAdminRoute requires super_admin role**
4. User without super_admin → **immediately redirected to /unauthorized**
5. This appears as "login causes redirect" to the user

**Root Cause:** `ProtectedRoute.tsx:63-65`
```typescript
// Extended grace period to 10 seconds for reliable state propagation
const justLoggedIn = isAuthenticated && authState.lastActivity &&
  (Date.now() - authState.lastActivity.getTime()) < 10000;
if (justLoggedIn) return;
```

This 10-second window prevents any permission checks, but **doesn't prevent redirects to /unauthorized** when the grace period expires.

---

## 2. Permission System Complexity Analysis

### Current Permission Structure

**📊 By The Numbers:**
- **49 different permissions** across 8 domains
- **11 different roles** (super_admin, admin, trainer, analyst, user, readonly, model_manager, data_steward, routing_admin, routing_operator, routing_auditor)
- **41 permission aliases** for backward compatibility
- **3 naming conventions** (dots, colons, underscores)

**Files:**
- `config/permissions.json` - 279 lines of permission definitions
- `src/components/security/rbac-shared.ts` - 148 lines of permission normalization logic

### Complexity Issues

#### 1. **Excessive Granularity** 🚨 HIGH IMPACT

**Example: Routing Permissions**
```json
"routing_admin": {
  "permissions": [
    "routing:audit", "routing:dry_run", "routing:health",
    "routing:profile:manage", "routing:profile:view", "routing:select"
  ]
},
"routing_operator": {
  "permissions": [
    "routing:dry_run", "routing:health",
    "routing:profile:view", "routing:select"
  ]
},
"routing_auditor": {
  "permissions": [
    "routing:audit", "routing:health", "routing:profile:view"
  ]
}
```

**Problem:** 3 separate roles for routing when 1-2 would suffice (routing:read vs routing:write)

#### 2. **Inconsistent Naming** 🚨 HIGH IMPACT

**41 Permission Aliases Required:**
```typescript
const PERMISSION_ALIASES: Record<string, Permission> = {
  'admin.users': 'admin:write',           // dot notation
  'admin_management': 'admin:write',       // underscore
  'admin.settings': 'admin:system',        // dot notation
  'system:config': 'admin:system',         // colon notation
  'system.config': 'admin:system',         // dot notation
  'system_config': 'admin:system',         // underscore
  // ... 35 more aliases
};
```

**Problem:** Multiple naming patterns indicate historical inconsistency and technical debt.

#### 3. **Permission Normalization Complexity** 🚨 MEDIUM IMPACT

**rbac-shared.ts:43-64** - Complex canonicalization logic:
```typescript
function canonicalizeToken(token: string): Permission {
  if (CANONICAL_PERMISSION_SET.has(token)) return token;

  const lower = token.toLowerCase();
  const alias = PERMISSION_ALIASES[lower];
  if (alias) return alias;

  if (CANONICAL_PERMISSION_SET.has(lower)) return lower;

  // Try converting dots/underscores to colons
  const colonCandidate = lower
    .replace(/\./g, ':')
    .replace(/__+/g, ':')
    .replace(/_/g, ':');
  if (CANONICAL_PERMISSION_SET.has(colonCandidate)) return colonCandidate;

  return token; // Return as-is if not found
}
```

**Problem:** This much normalization logic suggests the permission naming is inconsistent across the codebase.

#### 4. **Role Proliferation** 🚨 MEDIUM IMPACT

**11 Roles vs Real Requirements:**
```
✅ NECESSARY:
- super_admin (full access)
- admin (platform admin)
- user (standard user)

❓ QUESTIONABLE:
- trainer (specific to ML workflows)
- analyst (read-only with export)
- readonly (even more restricted read-only)

🚨 PROBABLY EXCESSIVE:
- model_manager (could be permission-based)
- data_steward (could be permission-based)
- routing_admin (could be permission-based)
- routing_operator (could be permission-based)
- routing_auditor (could be permission-based)
```

**Problem:** Roles should represent user types, not feature areas. Feature access should be permission-based.

---

## 3. Post-Login Permission Checks

### Where Permissions Are Checked

#### Frontend (Client-Side)

**1. ProtectedRoute Component** (`ProtectedRoute.tsx`)
```typescript
<ProtectedRoute
  requiredRole="super_admin"        // Optional role requirement
  requiredPermission="admin:write"  // Optional permission requirement
  redirectTo="/unauthorized"        // Where to redirect if unauthorized
>
  <AdminDashboard />
</ProtectedRoute>
```

**2. SuperAdminRoute Wrapper** (`SuperAdminRoute.tsx`)
```typescript
<SuperAdminRoute>  {/* Automatically requires super_admin role */}
  <SuperAdminDashboard />
</SuperAdminRoute>
```

**3. Auth Context Hooks** (`AuthContext.tsx`)
```typescript
const { hasRole, hasPermission, isAdmin, isSuperAdmin } = useAuth();

if (!hasRole('admin')) {
  return <AccessDenied />;
}
```

#### Backend (Server-Side)

**1. Admin Auth Middleware** (`lib/middleware/admin-auth.ts`)
```typescript
export async function withAdminAuth(
  request: NextRequest,
  handler: Function,
  options: {
    requiredRole?: 'admin' | 'super_admin';
    requiredPermission?: string;
    rateLimit?: { limit: number; windowMs: number };
  }
)
```

**2. Next.js Middleware** (`middleware.ts`)
```typescript
// Currently: NO authentication checks!
// Line 41: "No authentication checks - allow all requests"
```

⚠️ **Security Gap:** Next.js middleware doesn't enforce authentication, relying entirely on client-side checks.

---

## 4. What Permissions Are Being Requested

### Super Admin Access (49 permissions)

**From `config/permissions.json:52-103`:**
```json
"super_admin": {
  "permissions": [
    "admin:read", "admin:system", "admin:write",
    "audit:read",
    "data:delete", "data:export", "data:read", "data:write",
    "model:compatibility:check", "model:delete", "model:deploy",
    "model:download", "model:ensure", "model:gc", "model:health:check",
    "model:info", "model:license:accept", "model:license:manage",
    "model:license:view", "model:list", "model:pin", "model:quota:manage",
    "model:read", "model:registry:read", "model:registry:write",
    "model:remove", "model:unpin", "model:write",
    "routing:audit", "routing:dry_run", "routing:health",
    "routing:profile:manage", "routing:profile:view", "routing:select",
    "scheduler:execute", "scheduler:read", "scheduler:write",
    "security:evil_mode", "security:read", "security:write",
    "training:delete", "training:execute", "training:read", "training:write",
    "training_data:delete", "training_data:read", "training_data:write"
  ]
}
```

**Admin Role:** Same as super_admin (inherits_from: "super_admin")

**User Role (Basic Access):**
```json
"user": {
  "permissions": [
    "data:read",
    "model:info",
    "model:read",
    "training:read",
    "training_data:read"
  ]
}
```

### Common Permission Check Locations

**Searched codebase for permission usage:**
```bash
# Found 15 files using hasPermission/hasRole/requireAuth
- ProtectedRoute.tsx
- AdminRoute middleware
- usePermissions hook
- AuthContext
- AdminBreadcrumbs
- SuperAdminRoute
```

Most permission checks are for:
- `admin:read` - View admin dashboard
- `admin:write` - Modify users/settings
- `admin:system` - System configuration
- Various model/data permissions

---

## 5. Key Findings & Issues

### 🔴 Critical Issues

1. **Overly Complex RBAC System**
   - **Impact:** High maintenance cost, user confusion, development friction
   - **Evidence:** 49 permissions, 11 roles, 41 aliases
   - **Fix Priority:** HIGH

2. **Post-Login Race Condition Workaround**
   - **Impact:** 10-second permission check delay can cause confusing UX
   - **Location:** `ProtectedRoute.tsx:63-65`
   - **Fix Priority:** MEDIUM

3. **Missing Server-Side Route Protection**
   - **Impact:** Client-side permission checks can be bypassed
   - **Location:** `middleware.ts:41` explicitly skips auth
   - **Fix Priority:** HIGH (security)

### 🟡 Medium Issues

4. **Inconsistent Permission Naming**
   - **Impact:** Requires complex normalization logic, error-prone
   - **Evidence:** 41 aliases, 3 naming conventions
   - **Fix Priority:** MEDIUM

5. **Role vs Permission Confusion**
   - **Impact:** Feature-specific roles (routing_admin) should be permissions
   - **Evidence:** 8 out of 11 roles are feature-specific
   - **Fix Priority:** MEDIUM

6. **Unclear User Feedback**
   - **Impact:** Users don't know why they're seeing /unauthorized
   - **Location:** No custom unauthorized page with details
   - **Fix Priority:** LOW

---

## 6. Recommendations

### Immediate Fixes (This Week)

#### 1. Fix Build Error ✅
**Status:** Already resolved - path aliases configured correctly in tsconfig.json and next.config.js

#### 2. Reduce Grace Period 🔧
**File:** `src/components/auth/ProtectedRoute.tsx:63`

**Change:**
```typescript
// BEFORE: 10-second grace period
const justLoggedIn = isAuthenticated && authState.lastActivity &&
  (Date.now() - authState.lastActivity.getTime()) < 10000;

// AFTER: 1-second grace period
const justLoggedIn = isAuthenticated && authState.lastActivity &&
  (Date.now() - authState.lastActivity.getTime()) < 1000;
```

**Rationale:** 10 seconds is excessive. Modern state management should propagate in <100ms. 1 second provides ample buffer.

#### 3. Add Role-Based Default Redirects 🔧
**File:** `src/app/login/LoginPageClient.tsx:10-22`

**Change:**
```typescript
const handleLoginSuccess = async () => {
  const redirectFromQuery = searchParams?.get('redirectPath');
  const redirectFromStorage = sessionStorage.getItem('redirectAfterLogin');

  // NEW: Role-based default landing page
  const { user } = useAuth();
  const defaultPath = user?.role === 'super_admin' ? '/admin'
                    : user?.role === 'admin' ? '/admin'
                    : '/';

  const redirectPath = redirectFromQuery ?? redirectFromStorage ?? defaultPath;

  sessionStorage.removeItem('redirectAfterLogin');
  await new Promise((resolve) => setTimeout(resolve, 0));
  router.replace(redirectPath);
};
```

**Rationale:** Super admins expect to land on admin dashboard, not home page.

### Short-Term Improvements (This Month)

#### 4. Simplify Permission Structure 📋

**Create New Simplified Schema:**
```json
{
  "permissions": [
    "admin:read",      // View admin features
    "admin:write",     // Modify users/settings
    "data:read",       // View data
    "data:write",      // Modify data
    "data:delete",     // Delete data
    "model:read",      // View models
    "model:write",     // Deploy/modify models
    "audit:read"       // View audit logs
  ],
  "roles": {
    "super_admin": {
      "permissions": ["*"]  // All permissions
    },
    "admin": {
      "permissions": [
        "admin:read", "admin:write",
        "data:read", "data:write",
        "model:read", "model:write",
        "audit:read"
      ]
    },
    "user": {
      "permissions": ["data:read", "model:read"]
    }
  }
}
```

**Migration Steps:**
1. Create `config/permissions.v2.json` with simplified schema
2. Add backward compatibility layer in `rbac-shared.ts`
3. Gradually migrate codebase to use new permissions
4. Remove old permissions after 2 release cycles

**Reduction:** 49 permissions → 8 core permissions (84% reduction)

#### 5. Add Informative Unauthorized Page 🎨

**Create:** `src/app/unauthorized/page.tsx`
```typescript
'use client';

export default function UnauthorizedPage() {
  const searchParams = useSearchParams();
  const requiredRole = searchParams?.get('role');
  const requiredPermission = searchParams?.get('permission');
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Access Denied</CardTitle>
        </CardHeader>
        <CardContent>
          <p>You don't have permission to access this page.</p>

          {requiredRole && (
            <p className="mt-2">
              <strong>Required Role:</strong> {requiredRole}
              <br />
              <strong>Your Role:</strong> {user?.role || 'none'}
            </p>
          )}

          {requiredPermission && (
            <p className="mt-2">
              <strong>Required Permission:</strong> {requiredPermission}
            </p>
          )}

          <Button onClick={() => router.push('/')} className="mt-4">
            Return to Home
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Update ProtectedRoute redirects:**
```typescript
// Include role/permission in redirect URL
router.replace(`/unauthorized?role=${requiredRole}&permission=${requiredPermission}`);
```

### Long-Term Improvements (Next Quarter)

#### 6. Add Server-Side Authentication Middleware 🔐

**File:** `src/middleware.ts`

**Add authentication checks:**
```typescript
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protected routes that require authentication
  const protectedRoutes = ['/admin', '/chat', '/settings'];
  const isProtectedRoute = protectedRoutes.some(route =>
    pathname.startsWith(route)
  );

  if (isProtectedRoute) {
    const sessionCookie = request.cookies.get('session');
    if (!sessionCookie) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}
```

#### 7. Consolidate Role Checking Logic 🏗️

**Current State:** Permission checking scattered across:
- `AuthContext.tsx` - hasRole(), hasPermission()
- `usePermissions.ts` - duplicate logic
- `admin-auth.ts` - server-side duplicate
- `rbac-shared.ts` - core logic

**Proposed:** Single source of truth
```typescript
// lib/rbac/index.ts (new unified module)
export class RBACService {
  static hasRole(user: User, role: UserRole): boolean { }
  static hasPermission(user: User, permission: Permission): boolean { }
  static canAccess(user: User, resource: Resource): boolean { }
}
```

---

## 7. Testing Recommendations

### Test Cases to Add

1. **Login Flow Tests**
   ```typescript
   describe('Login with insufficient permissions', () => {
     it('should redirect user role to / after login', async () => {});
     it('should redirect admin role to /admin after login', async () => {});
     it('should preserve redirectPath query param', async () => {});
     it('should show permission error when accessing /admin as user', async () => {});
   });
   ```

2. **Grace Period Tests**
   ```typescript
   describe('ProtectedRoute grace period', () => {
     it('should not check permissions within 1 second of login', async () => {});
     it('should check permissions after 1 second grace period', async () => {});
   });
   ```

3. **Permission Normalization Tests**
   ```typescript
   describe('Permission normalization', () => {
     it('should normalize admin.users to admin:write', () => {});
     it('should normalize system_config to admin:system', () => {});
   });
   ```

---

## 8. Summary & Next Steps

### What's Wrong

1. ✅ **Build Error:** Module resolution for permissions.json (RESOLVED - aliases configured)
2. 🔴 **49 permissions** when 8-10 would suffice
3. 🔴 **11 roles** when 3-4 would suffice
4. 🔴 **41 permission aliases** indicating naming inconsistency
5. 🟡 **10-second grace period** causing delayed permission checks
6. 🟡 **No server-side route protection** in middleware
7. 🟡 **Confusing unauthorized page** with no context

### What to Do First

**Priority Order:**
1. ✅ **Build fix** - Already resolved
2. 🔧 **Reduce grace period** to 1 second (5 min fix)
3. 🔧 **Add role-based redirects** after login (15 min fix)
4. 🎨 **Create informative /unauthorized page** (30 min)
5. 📋 **Plan permission schema v2** (design session)
6. 🔐 **Add server-side middleware auth** (1-2 hours)
7. 🏗️ **Implement permission migration** (sprint-level effort)

### Metrics to Track

**Before:**
- Permissions: 49
- Roles: 11
- Permission aliases: 41
- Grace period: 10 seconds
- Server-side auth: ❌

**After (Target):**
- Permissions: 8-10
- Roles: 3-4
- Permission aliases: 0
- Grace period: 1 second
- Server-side auth: ✅

---

## Appendix: File Reference

### Key Files Examined

**Authentication:**
- `src/contexts/AuthContext.tsx` - Main auth logic (995 lines)
- `src/components/auth/LoginForm.tsx` - Login UI (396 lines)
- `src/app/login/LoginPageClient.tsx` - Login page redirect logic (26 lines)
- `src/lib/auth/session.ts` - Session management

**Authorization:**
- `src/components/auth/ProtectedRoute.tsx` - Route protection (135 lines)
- `src/components/auth/SuperAdminRoute.tsx` - Admin route wrapper (48 lines)
- `src/components/security/rbac-shared.ts` - RBAC core logic (148 lines)
- `src/components/security/usePermissions.ts` - Permission hook (60 lines)
- `src/lib/middleware/admin-auth.ts` - Server-side auth middleware (567 lines)

**Configuration:**
- `config/permissions.json` - Permission/role definitions (279 lines)
- `tsconfig.json` - Path aliases configuration
- `next.config.js` - Webpack aliases configuration (lines 224-225)
- `src/middleware.ts` - Next.js middleware (55 lines)

**Pages:**
- `src/app/page.tsx` - Home page with ProtectedRoute (282 lines)
- `src/app/admin/page.tsx` - Admin dashboard with SuperAdminRoute (21 lines)
- `src/app/chat/page.tsx` - Chat page with ProtectedRoute

---

**End of Audit Report**
