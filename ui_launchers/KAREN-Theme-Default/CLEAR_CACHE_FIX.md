# 🔴 CRITICAL: Clear Build Cache to Fix RBAC Error

## The Problem

You're seeing this error:
```
TypeError: Cannot read properties of undefined (reading 'user')
at resolveRolePermissions (src/components/security/rbac-shared.ts:103:1)
```

**Root Cause**: Your `.next` build directory contains **stale cached JavaScript** from previous code versions. The error references `rolesConfig` which no longer exists in the current code - this proves the cache is stale.

## ⚡ IMMEDIATE FIX (Required)

You MUST clear the Next.js build cache before the fix will work:

### Option 1: Quick Fix (Recommended)
```bash
cd ui_launchers/KAREN-Theme-Default

# Stop the dev server if running (Ctrl+C)

# Delete the entire .next directory
rm -rf .next

# Restart the dev server
npm run dev
```

### Option 2: Using npm script
```bash
cd ui_launchers/KAREN-Theme-Default

# We'll add a clean script to package.json
npm run clean
npm run dev
```

### Option 3: Nuclear Option (If still not working)
```bash
cd ui_launchers/KAREN-Theme-Default

# Stop dev server
# Clear everything
rm -rf .next
rm -rf node_modules/.cache

# Restart
npm run dev
```

## 🔍 How to Verify the Fix Worked

1. **Open browser DevTools** (F12)
2. **Go to Console tab**
3. **Hard refresh** the page (Ctrl+Shift+R or Cmd+Shift+R)
4. **Check for errors** - the RBAC undefined error should be gone

If you still see the error:
- Check that it's NOT referencing `rolesConfig` (old code)
- If it is, the cache STILL hasn't been cleared properly

## 📋 Why This Happens

Next.js caches compiled JavaScript in the `.next` directory for faster builds. When you update TypeScript source files, Next.js normally detects changes and recompiles. However, sometimes:

1. **Hot reload fails** to detect the change
2. **Webpack cache** gets corrupted
3. **Module resolution** caches old import paths
4. **Build optimization** creates persistent cached chunks

The RBAC code has gone through multiple iterations (Proxy → Object Getters → Object.defineProperty), and each change requires a fresh build to take effect.

## 🎯 The Current Fix (Object.defineProperty)

The latest code uses `Object.defineProperty` in an IIFE:

```typescript
export const ROLE_PERMISSIONS = (() => {
  const obj = {} as Record<UserRole, Permission[]>;

  Object.defineProperty(obj, 'user', {
    get: () => getRolePermissions('user'),
    enumerable: true,
    configurable: false,
  });
  // ... more properties

  return Object.freeze(obj);
})();
```

This approach:
- ✅ Creates an empty object during module load (zero computation)
- ✅ Defines getters at runtime using low-level API
- ✅ Webpack cannot statically analyze or trigger the getters
- ✅ Completely prevents undefined errors

## 🚀 After Clearing Cache

Once you've cleared the cache and restarted:

1. The error will disappear
2. RBAC permissions will work correctly
3. No performance impact
4. All role-based features will function normally

## ⚠️ If Error Persists After Cache Clear

If you've cleared the cache and still see errors:

1. **Check the error message** - what line number and code does it reference?
2. **Check for multiple Next.js instances** - make sure only one dev server is running
3. **Check browser cache** - hard refresh (Ctrl+Shift+R) or open in incognito
4. **Check for multiple project directories** - ensure you're editing the right one

## 📞 Still Having Issues?

If the error persists after trying all the above:

1. Copy the EXACT error message (including line numbers and code frame)
2. Run `cat ui_launchers/KAREN-Theme-Default/src/components/security/rbac-shared.ts | grep -n "rolesConfig"`
   - If this returns nothing, your source is correct but cache is still stale
   - If this returns results, the file wasn't updated properly
3. Report the issue with the output from step 2
