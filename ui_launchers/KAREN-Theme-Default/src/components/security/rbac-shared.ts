export type UserRole = 'user' | 'admin' | 'super_admin';
export type Permission = string;

type PermissionConfig = {
  permissions: readonly string[];
  roles: Record<string, { permissions?: readonly string[]; inherits_from?: string | null; description?: string }>;
};

const defaultPermissionConfig: PermissionConfig = {
  permissions: [],
  roles: {},
};

// Lazy initialization to avoid undefined issues during module loading
let permissionConfigCache: PermissionConfig | null = null;

function getPermissionConfig(): PermissionConfig {
  if (permissionConfigCache !== null) {
    return permissionConfigCache;
  }

  try {
    const raw = typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_PERMISSIONS_CONFIG;
    if (!raw) {
      permissionConfigCache = defaultPermissionConfig;
      return defaultPermissionConfig;
    }

    const parsed = JSON.parse(raw) as PermissionConfig;
    // Validate the parsed config has the required structure
    if (parsed && typeof parsed === 'object' && parsed.roles && parsed.permissions) {
      permissionConfigCache = parsed;
      return parsed;
    }

    console.warn('Invalid NEXT_PUBLIC_PERMISSIONS_CONFIG structure; using defaults');
    permissionConfigCache = defaultPermissionConfig;
    return defaultPermissionConfig;
  } catch (error) {
    console.warn(
      'Failed to parse NEXT_PUBLIC_PERMISSIONS_CONFIG; falling back to empty permissions set.',
      error
    );
    permissionConfigCache = defaultPermissionConfig;
    return defaultPermissionConfig;
  }
}

// Lazy getter for canonical permission set
let canonicalPermissionSetCache: Set<string> | null = null;

function getCanonicalPermissionSet(): Set<string> {
  if (canonicalPermissionSetCache === null) {
    const config = getPermissionConfig();
    canonicalPermissionSetCache = new Set(config?.permissions || []);
  }
  return canonicalPermissionSetCache;
}

const PERMISSION_ALIASES: Record<string, Permission> = {
  'admin.users': 'admin:write',
  'admin_management': 'admin:write',
  'admin.settings': 'admin:system',
  'admin_create': 'admin:system',
  'admin_delete': 'admin:system',
  'admin_edit': 'admin:system',
  'audit_logs': 'audit:read',
  'system.config': 'admin:system',
  'system.config.read': 'admin:system',
  'system.config.update': 'admin:system',
  'system.config_create': 'admin:system',
  'system.config_delete': 'admin:system',
  'system.config_update': 'admin:system',
  'system_config': 'admin:system',
  'system_config.read': 'admin:system',
  'system_config.update': 'admin:system',
  'system:config': 'admin:system',
  'system:config:read': 'admin:system',
  'system:config:update': 'admin:system',
  'system.config.manage': 'admin:system',
  'security_settings': 'security:write',
  'user.create': 'admin:write',
  'user.delete': 'admin:write',
  'user.edit': 'admin:write',
  'user_management': 'admin:read',
};

function canonicalizeToken(token: string): Permission {
  const canonicalSet = getCanonicalPermissionSet();

  if (canonicalSet.has(token)) {
    return token;
  }

  const lower = token.toLowerCase();
  const alias = PERMISSION_ALIASES[lower];
  if (alias) {
    return alias;
  }

  if (canonicalSet.has(lower)) {
    return lower;
  }

  const colonCandidate = lower.replace(/\./g, ':').replace(/__+/g, ':').replace(/_/g, ':');
  if (canonicalSet.has(colonCandidate)) {
    return colonCandidate;
  }

  return token;
}

export function normalizePermission(permission: string | null | undefined): Permission | null {
  if (!permission) return null;
  const trimmed = permission.trim();
  if (!trimmed) return null;
  return canonicalizeToken(trimmed);
}

export function normalizePermissionList(permissions?: readonly string[] | null): Permission[] {
  if (!permissions) return [];
  const normalized = new Set<Permission>();
  for (const permission of permissions) {
    const canonical = normalizePermission(permission);
    if (canonical) {
      normalized.add(canonical);
    }
  }
  return Array.from(normalized);
}

function resolveRolePermissions(role: UserRole): Permission[] {
  try {
    const config = getPermissionConfig();
    if (!config || !config.roles) {
      return [];
    }

    const entry = config.roles[role];
    if (!entry) {
      return [];
    }

    const inherited = entry.inherits_from && entry.inherits_from !== role
      ? resolveRolePermissions(entry.inherits_from as UserRole)
      : [];
    const current = normalizePermissionList(entry.permissions);
    return Array.from(new Set([...inherited, ...current]));
  } catch (error) {
    console.error(`Error resolving permissions for role ${role}:`, error);
    return [];
  }
}

// Lazy initialization of role permissions to avoid module loading issues
let rolePermissionsCache: Record<UserRole, Permission[]> | null = null;

function initializeRolePermissions(): void {
  if (rolePermissionsCache !== null) {
    return;
  }

  try {
    rolePermissionsCache = {
      user: resolveRolePermissions('user'),
      admin: resolveRolePermissions('admin'),
      super_admin: resolveRolePermissions('super_admin'),
    };
  } catch (error) {
    console.error('Failed to initialize role permissions, using empty defaults:', error);
    rolePermissionsCache = {
      user: [],
      admin: [],
      super_admin: [],
    };
  }
}

// Lazy getter function instead of direct export
function getRolePermissions(role: UserRole): Permission[] {
  initializeRolePermissions();
  return rolePermissionsCache![role] || [];
}

// Export object with getters for lazy initialization
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  get user(): Permission[] {
    return getRolePermissions('user');
  },
  get admin(): Permission[] {
    return getRolePermissions('admin');
  },
  get super_admin(): Permission[] {
    return getRolePermissions('super_admin');
  },
};

export const ROLE_HIERARCHY: Record<UserRole, number> = {
  user: 1,
  admin: 2,
  super_admin: 3,
} as const;

export function getHighestRole(roles: readonly string[] | undefined | null): UserRole {
  if (!roles || roles.length === 0) return 'user';
  if (roles.includes('super_admin')) return 'super_admin';
  if (roles.includes('admin')) return 'admin';
  return 'user';
}

export function getRoleDisplayName(role: UserRole | string): string {
  switch (role) {
    case 'super_admin':
      return 'Super Admin';
    case 'admin':
      return 'Admin';
    case 'user':
      return 'User';
    default:
      return role || 'Unknown';
  }
}

export function roleHasPermission(role: UserRole, permission: Permission): boolean {
  try {
    const canonical = normalizePermission(permission);
    if (!canonical) {
      return false;
    }
    const permissions = ROLE_PERMISSIONS[role];
    return Array.isArray(permissions) && permissions.includes(canonical);
  } catch (error) {
    console.error(`Error checking permission ${permission} for role ${role}:`, error);
    return false;
  }
}

export function roleHierarchy(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

export function canManageRole(managerRole: UserRole, targetRole: UserRole): boolean {
  if (managerRole === 'super_admin') return true;
  if (managerRole === 'admin') return targetRole === 'user';
  return false;
}

export function isValidRole(role: string): role is UserRole {
  return ['super_admin', 'admin', 'user'].includes(role);
}
