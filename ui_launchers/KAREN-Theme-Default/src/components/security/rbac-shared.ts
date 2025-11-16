import permissionsConfigFile from '@root-config/permissions.json';

export type UserRole =
  | 'user'
  | 'readonly'
  | 'analyst'
  | 'routing_auditor'
  | 'routing_operator'
  | 'routing_admin'
  | 'data_steward'
  | 'model_manager'
  | 'trainer'
  | 'admin'
  | 'super_admin';
export type Permission = string;

type RoleDefinition = {
  permissions: readonly string[];
  inherits_from: string | null;
  description?: string;
};

type PermissionConfig = {
  permissions: readonly string[];
  roles: Record<string, RoleDefinition>;
};

const BASELINE_ROLES: readonly UserRole[] = [
  'user',
  'readonly',
  'analyst',
  'routing_auditor',
  'routing_operator',
  'routing_admin',
  'data_steward',
  'model_manager',
  'trainer',
  'admin',
  'super_admin',
] as const;

const STATIC_PERMISSION_CONFIG = loadStaticPermissionConfig();

function loadStaticPermissionConfig(): PermissionConfig {
  const normalized = normalizeConfigSource(permissionsConfigFile, '@root-config/permissions.json');
  if (!normalized) {
    throw new Error('[rbac] Failed to load baseline permissions config from @root-config/permissions.json');
  }
  return normalized;
}

function ensurePermissionConfigShape(config?: unknown): PermissionConfig {
  if (!config || typeof config !== 'object') {
    return { permissions: [], roles: {} };
  }

  const raw = config as Record<string, unknown>;
  const permissions = Array.isArray(raw.permissions)
    ? raw.permissions.filter((value): value is string => typeof value === 'string')
    : [];

  const rawRoles = raw.roles && typeof raw.roles === 'object' ? (raw.roles as Record<string, unknown>) : {};
  const roles: Record<string, RoleDefinition> = {};

  for (const [roleName, value] of Object.entries(rawRoles)) {
    if (!value || typeof value !== 'object') {
      continue;
    }

    const roleRecord = value as Record<string, unknown>;
    const rolePermissions = Array.isArray(roleRecord.permissions)
      ? roleRecord.permissions.filter((permission): permission is string => typeof permission === 'string')
      : [];
    const inheritsFrom =
      typeof roleRecord.inherits_from === 'string'
        ? roleRecord.inherits_from
        : roleRecord.inherits_from === null
          ? null
          : null;
    const description = typeof roleRecord.description === 'string' ? roleRecord.description : undefined;

    roles[roleName] = {
      permissions: rolePermissions,
      inherits_from: inheritsFrom,
      description,
    };
  }

  return { permissions, roles };
}

function normalizeConfigSource(source: unknown, context: string): PermissionConfig | null {
  try {
    const shaped = ensurePermissionConfigShape(source);
    if (Object.keys(shaped.roles).length === 0) {
      throw new Error('No roles defined');
    }
    return normalizePermissionConfig(shaped);
  } catch (error) {
    console.warn(`[rbac] Unable to normalize permissions config from ${context}:`, error);
    return null;
  }
}

function normalizePermissionConfig(config: PermissionConfig): PermissionConfig {
  const roles = { ...config.roles };
  const missingRoles = BASELINE_ROLES.filter((role) => !roles[role]);
  if (missingRoles.length > 0) {
    throw new Error(`Missing baseline roles in permissions config: ${missingRoles.join(', ')}`);
  }

  const canonicalPermissions = Array.isArray(config.permissions)
    ? Array.from(new Set(config.permissions))
    : [];

  const adminEntry = roles.admin!;
  const normalizedAdmin: RoleDefinition = {
    ...adminEntry,
    inherits_from:
      adminEntry.inherits_from && adminEntry.inherits_from !== 'super_admin'
        ? adminEntry.inherits_from
        : null,
  };

  const superAdminEntry = roles.super_admin!;
  const normalizedSuperAdmin: RoleDefinition = {
    ...superAdminEntry,
    inherits_from: superAdminEntry.inherits_from ?? 'admin',
  };

  const aggregated = new Set<string>(normalizedSuperAdmin.permissions ?? []);
  for (const [roleName, entry] of Object.entries(roles)) {
    if (roleName === 'super_admin') {
      continue;
    }
    for (const permission of entry.permissions ?? []) {
      aggregated.add(permission);
    }
  }
  for (const permission of canonicalPermissions) {
    aggregated.add(permission);
  }
  normalizedSuperAdmin.permissions = Array.from(aggregated);

  return {
    permissions: canonicalPermissions,
    roles: {
      ...roles,
      admin: normalizedAdmin,
      super_admin: normalizedSuperAdmin,
    },
  };
}

// Lazy initialization to avoid undefined issues during module loading
let permissionConfigCache: PermissionConfig | null = null;
let permissionConfigAuditLogged = false;

function getPermissionConfig(): PermissionConfig {
  if (permissionConfigCache !== null) {
    return permissionConfigCache;
  }

  const envConfig = tryLoadEnvPermissionConfig();
  permissionConfigCache = envConfig ?? STATIC_PERMISSION_CONFIG;
  auditPermissionConfig(permissionConfigCache);
  return permissionConfigCache;
}

function tryLoadEnvPermissionConfig(): PermissionConfig | null {
  if (typeof process === 'undefined') {
    return null;
  }
  const raw = process.env?.NEXT_PUBLIC_PERMISSIONS_CONFIG;
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as unknown;
    return normalizeConfigSource(parsed, 'NEXT_PUBLIC_PERMISSIONS_CONFIG');
  } catch (error) {
    console.warn('Failed to parse NEXT_PUBLIC_PERMISSIONS_CONFIG; falling back to static permissions file.', error);
    return null;
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

function resolveRolePermissions(role: string, visited: Set<string> = new Set()): Permission[] {
  const config = getPermissionConfig();
  const roles = config.roles ?? {};
  const entry = roles[role];
  if (!entry) {
    throw new Error(`[rbac] Attempted to resolve permissions for unknown role "${role}".`);
  }

  if (entry.inherits_from && !roles[entry.inherits_from]) {
    throw new Error(
      `[rbac] Role "${role}" inherits from unknown role "${entry.inherits_from}".`
    );
  }

  if (visited.has(role)) {
    const chain = Array.from(visited).concat(role).join(' -> ');
    throw new Error(`[rbac] Circular role inheritance detected: ${chain}`);
  }

  const nextVisited = new Set(visited).add(role);
  const inherited = entry.inherits_from && entry.inherits_from !== role
    ? resolveRolePermissions(entry.inherits_from, nextVisited)
    : [];
  const current = normalizePermissionList(entry.permissions);
  return mergePermissionLists(inherited, current);
}

// Lazy initialization of role permissions to avoid module loading issues
let rolePermissionsCache: Record<string, Permission[]> | null = null;

function initializeRolePermissions(): void {
  if (rolePermissionsCache !== null) {
    return;
  }

  const config = getPermissionConfig();
  const computed: Record<string, Permission[]> = {};
  for (const roleName of Object.keys(config.roles)) {
    computed[roleName] = resolveRolePermissions(roleName);
  }
  rolePermissionsCache = computed;
}

// Function-based API to get role permissions (prevents any module-level initialization)
export function getRolePermissions(role: UserRole | string): Permission[] {
  initializeRolePermissions();
  return rolePermissionsCache?.[role] || [];
}

const ROLE_PERMISSIONS_PROXY = new Proxy({} as Record<string, Permission[]>, {
  get(_target, prop: string | symbol) {
    if (typeof prop !== 'string') {
      return undefined;
    }
    return getRolePermissions(prop);
  },
  ownKeys() {
    return Object.keys(getPermissionConfig().roles);
  },
  getOwnPropertyDescriptor(_target, prop: string | symbol) {
    if (typeof prop !== 'string') {
      return undefined;
    }
    return {
      configurable: false,
      enumerable: true,
      value: getRolePermissions(prop),
      writable: false,
    };
  },
});

export const ROLE_PERMISSIONS = ROLE_PERMISSIONS_PROXY as Record<string, Permission[]>;

export function getHighestRole(roles: readonly string[] | undefined | null): UserRole {
  if (!roles || roles.length === 0) return 'user';

  let highestRole: UserRole = 'user';
  let highestRank = ROLE_HIERARCHY[highestRole];

  for (const role of roles) {
    if (!role || !isValidRole(role)) {
      continue;
    }
    const rank = ROLE_HIERARCHY[role];
    if (rank > highestRank) {
      highestRank = rank;
      highestRole = role;
    }
  }

  return highestRole;
}

export function getRoleDisplayName(role: UserRole | string): string {
  switch (role) {
    case 'super_admin':
      return 'Super Admin';
    case 'admin':
      return 'Admin';
    case 'trainer':
      return 'Trainer';
    case 'analyst':
      return 'Analyst';
    case 'readonly':
      return 'Read Only';
    case 'model_manager':
      return 'Model Manager';
    case 'data_steward':
      return 'Data Steward';
    case 'routing_admin':
      return 'Routing Admin';
    case 'routing_operator':
      return 'Routing Operator';
    case 'routing_auditor':
      return 'Routing Auditor';
    case 'user':
      return 'User';
    default:
      return role || 'Unknown';
  }
}

export function roleHasPermission(role: UserRole, permission: Permission): boolean {
  const canonical = normalizePermission(permission);
  if (!canonical) {
    return false;
  }
  const permissions = getRolePermissions(role);
  return Array.isArray(permissions) && permissions.includes(canonical);
}

export function roleHierarchy(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

export function canManageRole(managerRole: UserRole, targetRole: UserRole): boolean {
  if (managerRole === targetRole) {
    return false;
  }
  return ROLE_HIERARCHY[managerRole] > ROLE_HIERARCHY[targetRole];
}

export function isValidRole(role: string): role is UserRole {
  return Object.prototype.hasOwnProperty.call(ROLE_HIERARCHY, role);
}

function mergePermissionLists(...lists: Permission[][]): Permission[] {
  const normalized = new Set<Permission>();
  for (const list of lists) {
    for (const permission of list) {
      normalized.add(permission);
    }
  }
  return Array.from(normalized);
}

function auditPermissionConfig(config: PermissionConfig): void {
  if (permissionConfigAuditLogged) {
    return;
  }
  permissionConfigAuditLogged = true;

  const canonicalPermissions = new Set(config.permissions);
  const missingRoles = BASELINE_ROLES.filter((role) => !config.roles[role]);
  if (missingRoles.length > 0) {
    console.warn(
      '[rbac] Missing baseline roles in permissions config:',
      missingRoles.join(', ')
    );
  }

  for (const [roleName, entry] of Object.entries(config.roles)) {
    if (entry.inherits_from && !config.roles[entry.inherits_from]) {
      console.warn(`[rbac] Role "${roleName}" inherits from unknown role "${entry.inherits_from}".`);
    }

    const invalidPermissions = (entry.permissions ?? []).filter(
      (permission) => !canonicalPermissions.has(permission)
    );
    if (invalidPermissions.length > 0) {
      console.warn(
        `[rbac] Role "${roleName}" references permissions not present in the canonical list: ${invalidPermissions.join(', ')}`
      );
    }
  }
}

export const ROLE_HIERARCHY: Record<UserRole, number> = {
  user: 1,
  readonly: 2,
  analyst: 3,
  routing_auditor: 4,
  routing_operator: 5,
  routing_admin: 6,
  data_steward: 7,
  model_manager: 8,
  trainer: 9,
  admin: 10,
  super_admin: 11,
} as const;
