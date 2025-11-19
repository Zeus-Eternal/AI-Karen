export type UserRole =
  | 'guest'
  | 'readonly'
  | 'user'
  | 'analyst'
  | 'routing_auditor'
  | 'routing_operator'
  | 'support_agent'
  | 'data_steward'
  | 'model_manager'
  | 'content_manager'
  | 'trainer'
  | 'security_audit'
  | 'routing_admin'
  | 'data_admin'
  | 'model_admin'
  | 'security_admin'
  | 'system_admin'
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

// Define all available roles in the system with a clear hierarchy
const BASELINE_ROLES: readonly UserRole[] = [
  // Base roles (no inheritance)
  'guest',           // Unauthenticated users with minimal access
  'readonly',        // Read-only access to non-sensitive data
  'user',            // Standard authenticated user
  
  // Specialized roles (inherit from user or readonly)
  'analyst',         // Data analysis capabilities
  'routing_auditor', // View routing information
  'routing_operator', // Basic routing operations
  'data_steward',    // Manage datasets and training data
  'model_manager',   // Manage model lifecycle
  'trainer',         // Create and train models
  'security_audit',  // Security and compliance monitoring
  'support_agent',   // Customer support capabilities
  'content_manager', // Manage content and documentation
  
  // Administrative roles
  'routing_admin',   // Full routing administration
  'data_admin',      // Full data administration
  'model_admin',     // Full model administration
  'security_admin',  // Security administration
  'system_admin',    // System-wide administration
  'admin',           // Full administrative access
  'super_admin',     // Unrestricted access (includes all permissions)
] as const;

// Define all possible permissions in the system
type SystemPermission = 
  // System and admin permissions
  | 'system:access' | 'system:admin' | 'system:settings:read' | 'system:settings:write'
  
  // User management
  | 'user:create' | 'user:read' | 'user:update' | 'user:delete' | 'user:impersonate'
  
  // Data permissions
  | 'data:read' | 'data:create' | 'data:update' | 'data:delete' | 'data:export' | 'data:import'
  
  // Model permissions
  | 'model:read' | 'model:create' | 'model:update' | 'model:delete' | 'model:deploy' | 'model:train'
  | 'model:version' | 'model:promote' | 'model:rollback' | 'model:metrics'
  
  // Training permissions
  | 'training:create' | 'training:read' | 'training:update' | 'training:delete' | 'training:execute'
  | 'training:monitor' | 'training:stop'
  
  // Routing permissions
  | 'routing:read' | 'routing:configure' | 'routing:deploy' | 'routing:test' | 'routing:audit'
  
  // Security permissions
  | 'security:read' | 'security:configure' | 'security:audit' | 'security:incident:view' 
  | 'security:incident:manage' | 'security:policy:manage'
  
  // API and Integration permissions
  | 'api:access' | 'api:manage' | 'integration:create' | 'integration:manage' | 'webhook:manage';

// Create a default permission config that can be used as a fallback
const DEFAULT_PERMISSION_CONFIG: PermissionConfig = {
  permissions: [
    'admin:read',
    'admin:system',
    'admin:write',
    'audit:read',
    'data:delete',
    'data:export',
    'data:read',
    'data:write',
    'model:compatibility:check',
    'model:delete',
    'model:deploy',
    'model:download',
    'model:ensure',
    'model:gc',
    'model:health:check',
    'model:info',
    'model:license:accept',
    'model:license:manage',
    'model:license:view',
    'model:list',
    'model:pin',
    'model:quota:manage',
    'model:read',
    'model:registry:read',
    'model:registry:write',
    'model:remove',
    'model:unpin',
    'model:write',
    'routing:audit',
    'routing:dry_run',
    'routing:health',
    'routing:profile:manage',
    'routing:profile:view',
    'routing:select',
    'scheduler:execute',
    'scheduler:read',
    'scheduler:write',
    'security:evil_mode',
    'security:read',
    'security:write',
    'training:delete',
    'training:execute',
    'training:read',
    'training:write',
    'training_data:delete',
    'training_data:read',
    'training_data:write'
  ],
  roles: {
    user: {
      description: "Standard platform user",
      inherits_from: null,
      permissions: [
        "data:read",
        "model:info",
        "model:read",
        "training:read",
        "training_data:read"
      ]
    },
    readonly: {
      description: "Read only visibility",
      inherits_from: null,
      permissions: [
        "model:info",
        "model:read",
        "training:read"
      ]
    },
    analyst: {
      description: "Read focused analyst role",
      inherits_from: null,
      permissions: [
        "audit:read",
        "data:export",
        "data:read",
        "model:info",
        "model:read",
        "scheduler:read",
        "training:read",
        "training_data:read"
      ]
    },
    routing_auditor: {
      description: "Read only routing insights",
      inherits_from: null,
      permissions: [
        "routing:audit",
        "routing:health",
        "routing:profile:view"
      ]
    },
    routing_operator: {
      description: "Operational routing control",
      inherits_from: null,
      permissions: [
        "routing:dry_run",
        "routing:health",
        "routing:profile:view",
        "routing:select"
      ]
    },
    routing_admin: {
      description: "Full routing administration",
      inherits_from: null,
      permissions: [
        "routing:audit",
        "routing:dry_run",
        "routing:health",
        "routing:profile:manage",
        "routing:profile:view",
        "routing:select"
      ]
    },
    data_steward: {
      description: "Manage datasets and training corpora",
      inherits_from: null,
      permissions: [
        "data:delete",
        "data:export",
        "data:read",
        "data:write",
        "training_data:delete",
        "training_data:read",
        "training_data:write"
      ]
    },
    model_manager: {
      description: "Operational model management",
      inherits_from: null,
      permissions: [
        "model:compatibility:check",
        "model:download",
        "model:ensure",
        "model:gc",
        "model:health:check",
        "model:info",
        "model:license:accept",
        "model:license:view",
        "model:list",
        "model:pin",
        "model:read",
        "model:remove",
        "model:unpin",
        "model:write"
      ]
    },
    trainer: {
      description: "Training specialist with model and data management access",
      inherits_from: null,
      permissions: [
        "data:export",
        "data:read",
        "data:write",
        "model:deploy",
        "model:download",
        "model:ensure",
        "model:info",
        "model:read",
        "model:write",
        "scheduler:read",
        "scheduler:write",
        "training:execute",
        "training:read",
        "training:write",
        "training_data:read",
        "training_data:write"
      ]
    },
    admin: {
      description: "Platform administrator",
      inherits_from: null,
      permissions: [
        "admin:read",
        "admin:system",
        "admin:write",
        "audit:read",
        "data:delete",
        "data:export",
        "data:read",
        "data:write",
        "model:compatibility:check",
        "model:delete",
        "model:deploy",
        "model:download",
        "model:ensure",
        "model:gc",
        "model:health:check",
        "model:info",
        "model:license:accept",
        "model:license:manage",
        "model:license:view",
        "model:list",
        "model:pin",
        "model:quota:manage",
        "model:read",
        "model:registry:read",
        "model:registry:write",
        "model:remove",
        "model:unpin",
        "model:write",
        "routing:audit",
        "routing:dry_run",
        "routing:health",
        "routing:profile:manage",
        "routing:profile:view",
        "routing:select",
        "scheduler:execute",
        "scheduler:read",
        "scheduler:write",
        "security:read",
        "security:write",
        "training:delete",
        "training:execute",
        "training:read",
        "training:write",
        "training_data:delete",
        "training_data:read",
        "training_data:write"
      ]
    },
    super_admin: {
      description: "Highest privilege role with unrestricted access",
      inherits_from: "admin",
      permissions: [
        "admin:read",
        "admin:system",
        "admin:write",
        "audit:read",
        "data:delete",
        "data:export",
        "data:read",
        "data:write",
        "model:compatibility:check",
        "model:delete",
        "model:deploy",
        "model:download",
        "model:ensure",
        "model:gc",
        "model:health:check",
        "model:info",
        "model:license:accept",
        "model:license:manage",
        "model:license:view",
        "model:list",
        "model:pin",
        "model:quota:manage",
        "model:read",
        "model:registry:read",
        "model:registry:write",
        "model:remove",
        "model:unpin",
        "model:write",
        "routing:audit",
        "routing:dry_run",
        "routing:health",
        "routing:profile:manage",
        "routing:profile:view",
        "routing:select",
        "scheduler:execute",
        "scheduler:read",
        "scheduler:write",
        "security:evil_mode",
        "security:read",
        "security:write",
        "training:delete",
        "training:execute",
        "training:read",
        "training:write",
        "training_data:delete",
        "training_data:read",
        "training_data:write"
      ]
    },
    guest: {
      description: "Unauthenticated users with minimal access",
      inherits_from: null,
      permissions: [
        "model:info"
      ]
    },
    security_audit: {
      description: "Security and compliance monitoring",
      inherits_from: "analyst",
      permissions: [
        "audit:read",
        "data:export",
        "data:read",
        "model:info",
        "model:read",
        "security:read",
        "training:read",
        "training_data:read"
      ]
    },
    support_agent: {
      description: "Customer support capabilities",
      inherits_from: "user",
      permissions: [
        "data:read",
        "model:info",
        "model:read",
        "training:read",
        "training_data:read"
      ]
    },
    content_manager: {
      description: "Manage content and documentation",
      inherits_from: "data_steward",
      permissions: [
        "data:delete",
        "data:export",
        "data:read",
        "data:write",
        "training_data:delete",
        "training_data:read",
        "training_data:write"
      ]
    },
    data_admin: {
      description: "Full data administration",
      inherits_from: "admin",
      permissions: [
        "admin:read",
        "admin:system",
        "admin:write",
        "audit:read",
        "data:delete",
        "data:export",
        "data:read",
        "data:write",
        "model:info",
        "model:read",
        "training:delete",
        "training:read",
        "training:write",
        "training_data:delete",
        "training_data:read",
        "training_data:write"
      ]
    },
    model_admin: {
      description: "Full model administration",
      inherits_from: "admin",
      permissions: [
        "admin:read",
        "admin:system",
        "admin:write",
        "audit:read",
        "model:compatibility:check",
        "model:delete",
        "model:deploy",
        "model:download",
        "model:ensure",
        "model:gc",
        "model:health:check",
        "model:info",
        "model:license:accept",
        "model:license:manage",
        "model:license:view",
        "model:list",
        "model:pin",
        "model:quota:manage",
        "model:read",
        "model:registry:read",
        "model:registry:write",
        "model:remove",
        "model:unpin",
        "model:write",
        "training:execute",
        "training:read",
        "training:write"
      ]
    },
    security_admin: {
      description: "Security administration",
      inherits_from: "admin",
      permissions: [
        "admin:read",
        "admin:system",
        "admin:write",
        "audit:read",
        "security:evil_mode",
        "security:read",
        "security:write"
      ]
    },
    system_admin: {
      description: "System-wide administration",
      inherits_from: "admin",
      permissions: [
        "admin:read",
        "admin:system",
        "admin:write",
        "audit:read",
        "routing:audit",
        "routing:dry_run",
        "routing:health",
        "routing:profile:manage",
        "routing:profile:view",
        "routing:select",
        "scheduler:execute",
        "scheduler:read",
        "scheduler:write",
        "security:read",
        "security:write"
      ]
    }
  }
};


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
    
    // Safety check: if shaped is undefined, return null
    if (!shaped) {
      console.error(`[rbac] Unable to shape permissions config from ${context}`);
      return null;
    }
    
    // Safety check: if shaped.roles is undefined, return null
    if (!shaped.roles || Object.keys(shaped.roles).length === 0) {
      console.error(`[rbac] No roles defined in permissions config from ${context}`);
      return null;
    }
    
    return normalizePermissionConfig(shaped);
  } catch (error) {
    console.warn(`[rbac] Unable to normalize permissions config from ${context}:`, error);
    return null;
  }
}

function normalizePermissionConfig(config: PermissionConfig): PermissionConfig {
  console.log('[DEBUG] normalizePermissionConfig called with config:', config);
  
  try {
    // Safety check: if config is undefined, return a default config
    if (!config) {
      console.error('[DEBUG] config is undefined in normalizePermissionConfig, returning default config');
      return {
        permissions: [],
        roles: {}
      };
    }
    
    // Additional safety check for config.roles
    if (!config.roles) {
      console.error('[DEBUG] config.roles is undefined in normalizePermissionConfig, returning default config');
      return {
        permissions: config.permissions || [],
        roles: {}
      };
    }
    
    // Additional safety check for config.permissions
    if (!config.permissions) {
      console.error('[DEBUG] config.permissions is undefined in normalizePermissionConfig, using empty array');
      config.permissions = [];
    }
    
    // Create a deep copy of roles to avoid modifying the original
    const roles: Record<string, RoleDefinition> = JSON.parse(JSON.stringify(config.roles));
    const missingRoles = BASELINE_ROLES.filter((role) => !roles[role]);
    
    if (missingRoles.length > 0) {
      console.warn(`[rbac] Missing baseline roles in permissions config: ${missingRoles.join(', ')}. Using safe fallbacks.`);
      // Instead of throwing, create fallback roles
      for (const role of missingRoles) {
        roles[role] = {
          permissions: [],
          inherits_from: null
        };
      }
    }

    const canonicalPermissions = Array.isArray(config.permissions)
      ? Array.from(new Set(config.permissions))
      : [];

    // Safety check for admin entry
    const adminEntry = roles.admin || {
      permissions: [],
      inherits_from: null
    };
    
    const normalizedAdmin: RoleDefinition = {
      ...adminEntry,
      inherits_from:
        adminEntry.inherits_from && adminEntry.inherits_from !== 'super_admin'
          ? adminEntry.inherits_from
          : null,
    };

    // Safety check for super_admin entry
    const superAdminEntry = roles.super_admin || {
      permissions: [],
      inherits_from: 'admin'
    };
    
    const normalizedSuperAdmin: RoleDefinition = {
      ...superAdminEntry,
      inherits_from: superAdminEntry.inherits_from ?? 'admin',
    };

    const aggregated = new Set<string>(normalizedSuperAdmin.permissions ?? []);
    for (const [roleName, entry] of Object.entries(roles)) {
      if (roleName === 'super_admin') {
        continue;
      }
      // Safety check for entry and entry permissions
      if (!entry) {
        console.warn(`[rbac] Role "${roleName}" has undefined entry. Skipping.`);
        continue;
      }
      const entryPermissions = Array.isArray(entry.permissions) ? entry.permissions : [];
      for (const permission of entryPermissions) {
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
  } catch (error) {
    console.error('[DEBUG] Error in normalizePermissionConfig:', error);
    // Return a safe fallback config
    return {
      permissions: [],
      roles: {
        admin: { permissions: [], inherits_from: null },
        super_admin: { permissions: [], inherits_from: 'admin' }
      }
    };
  }
}

// Lazy initialization to avoid undefined issues during module loading
let permissionConfigCache: PermissionConfig | null = null;
let permissionConfigAuditLogged = false;

function getPermissionConfig(): PermissionConfig {
  if (permissionConfigCache !== null) {
    return permissionConfigCache;
  }

  try {
    const envConfig = tryLoadEnvPermissionConfig();
    permissionConfigCache = envConfig ?? DEFAULT_PERMISSION_CONFIG;
    
    // Safety check: if permissionConfigCache is undefined, create a default config
    if (!permissionConfigCache) {
      console.error('[rbac] permissionConfigCache is undefined in getPermissionConfig. Creating default config.');
      permissionConfigCache = DEFAULT_PERMISSION_CONFIG;
    }
    
    // Audit the permission config for missing roles or invalid permissions
    if (permissionConfigCache && permissionConfigCache.roles) {
      const missingRoles = BASELINE_ROLES.filter((role) => !permissionConfigCache || !permissionConfigCache.roles || !permissionConfigCache.roles[role]);
      if (missingRoles.length > 0) {
        console.warn(`[rbac] Missing baseline roles in permissions config: ${missingRoles.join(', ')}. Using safe fallbacks.`);
      }
    }
    return permissionConfigCache;
  } catch (error) {
    console.error('[rbac] Error in getPermissionConfig:', error);
    // Return a default config if there's an error
    return DEFAULT_PERMISSION_CONFIG;
  }
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

function resolveRolePermissions(role: string | undefined | null, visited: Set<string> = new Set()): Permission[] {
  // Return empty array if role is not provided or invalid
  if (!role || typeof role !== 'string') {
    console.warn('[rbac] Invalid or missing role provided to resolveRolePermissions');
    return [];
  }
  try {
    // Define role types for better type safety
    interface RoleDefinition {
      description: string;
      inherits_from: string | null;
      permissions: string[];
    }

    // Local copy of roles with type safety
    const roles: Record<string, RoleDefinition> = {
      user: {
        description: "Standard platform user",
        inherits_from: null,
        permissions: [
          "data:read",
          "model:info",
          "model:read",
          "training:read",
          "training_data:read"
        ]
      },
      readonly: {
        description: "Read only visibility",
        inherits_from: null,
        permissions: [
          "model:info",
          "model:read",
          "training:read"
        ]
      },
      analyst: {
        description: "Read focused analyst role",
        inherits_from: null,
        permissions: [
          "audit:read",
          "data:export",
          "data:read",
          "model:info",
          "model:read",
          "scheduler:read",
          "training:read",
          "training_data:read"
        ]
      },
      routing_auditor: {
        description: "Read only routing insights",
        inherits_from: null,
        permissions: [
          "routing:audit",
          "routing:health",
          "routing:profile:view"
        ]
      },
      routing_operator: {
        description: "Operational routing control",
        inherits_from: null,
        permissions: [
          "routing:dry_run",
          "routing:health",
          "routing:profile:view",
          "routing:select"
        ]
      },
      routing_admin: {
        description: "Full routing administration",
        inherits_from: null,
        permissions: [
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select"
        ]
      },
      data_steward: {
        description: "Manage datasets and training corpora",
        inherits_from: null,
        permissions: [
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      },
      model_manager: {
        description: "Operational model management",
        inherits_from: null,
        permissions: [
          "model:compatibility:check",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:read",
          "model:remove",
          "model:unpin",
          "model:write"
        ]
      },
      trainer: {
        description: "Training specialist with model and data management access",
        inherits_from: null,
        permissions: [
          "data:export",
          "data:read",
          "data:write",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:info",
          "model:read",
          "model:write",
          "scheduler:read",
          "scheduler:write",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:read",
          "training_data:write"
        ]
      },
      admin: {
        description: "Platform administrator",
        inherits_from: null,
        permissions: [
          "admin:read",
          "admin:system",
          "admin:write",
          "audit:read",
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "model:compatibility:check",
          "model:delete",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:manage",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:quota:manage",
          "model:read",
          "model:registry:read",
          "model:registry:write",
          "model:remove",
          "model:unpin",
          "model:write",
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select",
          "scheduler:execute",
          "scheduler:read",
          "scheduler:write",
          "security:read",
          "security:write",
          "training:delete",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      },
      super_admin: {
        description: "Highest privilege role with unrestricted access",
        inherits_from: "admin",
        permissions: [
          "admin:read",
          "admin:system",
          "admin:write",
          "audit:read",
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "model:compatibility:check",
          "model:delete",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:manage",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:quota:manage",
          "model:read",
          "model:registry:read",
          "model:registry:write",
          "model:remove",
          "model:unpin",
          "model:write",
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select",
          "scheduler:execute",
          "scheduler:read",
          "scheduler:write",
          "security:evil_mode",
          "security:read",
          "security:write",
          "training:delete",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      }
    };
    
    // Safety check: if role is undefined, return empty permissions
    if (!role) {
      console.error(`[rbac] Role is undefined in resolveRolePermissions. Returning empty permissions.`);
      return [];
    }
    
    // Safety check: if role doesn't exist in roles, return empty permissions
    if (!roles[role]) {
      console.error(`[rbac] Role "${role}" does not exist in roles. Returning empty permissions.`);
      return [];
    }
    
    const entry = roles[role];
    
    // Safety check: if entry is undefined, return empty permissions
    if (!entry) {
      console.error(`[rbac] Entry is undefined for role "${role}". Returning empty permissions.`);
      return [];
    }

    // Safety check: if entry.permissions is undefined, use empty array
    const permissions = entry.permissions || [];
    if (!Array.isArray(permissions)) {
      console.error(`[rbac] Permissions for role "${role}" is not an array. Using empty array.`);
      return [];
    }

    // Safety check: if inherits_from is undefined, set it to null
    if (entry.inherits_from === undefined) {
      entry.inherits_from = null;
    }

    // Extra safety check: if entry.inherits_from is null, we don't need to do anything
    if (entry.inherits_from === null) {
      // No inheritance, just continue with current permissions
    }

    if (entry.inherits_from && !roles[entry.inherits_from]) {
      console.error(`[rbac] Role "${role}" inherits from unknown role "${entry.inherits_from}". Ignoring inheritance.`);
      // Instead of throwing, just ignore the inheritance and continue with current permissions
    }

    if (visited.has(role)) {
      const chain = Array.from(visited).concat(role).join(' -> ');
      console.error(`[rbac] Circular role inheritance detected: ${chain}. Breaking the cycle.`);
      // Instead of throwing, break the cycle by returning current permissions
    }

    const nextVisited = new Set(visited).add(role);
    const inherited = entry.inherits_from && entry.inherits_from !== role && roles[entry.inherits_from]
      ? resolveRolePermissions(entry.inherits_from, nextVisited)
      : [];
    
    // Safety check: if entry.permissions is undefined, use empty array
    const current = normalizePermissionList(permissions);
    
    // Merge inherited and current permissions
    const merged = new Set<Permission>();
    for (const perm of inherited) {
      merged.add(perm);
    }
    for (const perm of current) {
      merged.add(perm);
    }
    return Array.from(merged);
  } catch (error) {
    // Log the error with more context
    console.error(`[rbac] Error in resolveRolePermissions for role "${role}":`, error);
    // Return empty array to prevent breaking the application
    return [];
  } finally {
    // Clean up the visited set to prevent memory leaks
    if (role) {
      visited.delete(role);
    }
  }
}

// Lazy initialization of role permissions to avoid module loading issues
let rolePermissionsCache: Record<string, Permission[]> | null = null;

function initializeRolePermissions(): void {
  if (rolePermissionsCache !== null) {
    return;
  }

  try {
    // Use the same local copy of roles as in resolveRolePermissions
    const roles = {
      user: {
        description: "Standard platform user",
        inherits_from: null,
        permissions: [
          "data:read",
          "model:info",
          "model:read",
          "training:read",
          "training_data:read"
        ]
      },
      readonly: {
        description: "Read only visibility",
        inherits_from: null,
        permissions: [
          "model:info",
          "model:read",
          "training:read"
        ]
      },
      analyst: {
        description: "Read focused analyst role",
        inherits_from: null,
        permissions: [
          "audit:read",
          "data:export",
          "data:read",
          "model:info",
          "model:read",
          "scheduler:read",
          "training:read",
          "training_data:read"
        ]
      },
      routing_auditor: {
        description: "Read only routing insights",
        inherits_from: null,
        permissions: [
          "routing:audit",
          "routing:health",
          "routing:profile:view"
        ]
      },
      routing_operator: {
        description: "Operational routing control",
        inherits_from: null,
        permissions: [
          "routing:dry_run",
          "routing:health",
          "routing:profile:view",
          "routing:select"
        ]
      },
      routing_admin: {
        description: "Full routing administration",
        inherits_from: null,
        permissions: [
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select"
        ]
      },
      data_steward: {
        description: "Manage datasets and training corpora",
        inherits_from: null,
        permissions: [
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      },
      model_manager: {
        description: "Operational model management",
        inherits_from: null,
        permissions: [
          "model:compatibility:check",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:read",
          "model:remove",
          "model:unpin",
          "model:write"
        ]
      },
      trainer: {
        description: "Training specialist with model and data management access",
        inherits_from: null,
        permissions: [
          "data:export",
          "data:read",
          "data:write",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:info",
          "model:read",
          "model:write",
          "scheduler:read",
          "scheduler:write",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:read",
          "training_data:write"
        ]
      },
      admin: {
        description: "Platform administrator",
        inherits_from: null,
        permissions: [
          "admin:read",
          "admin:system",
          "admin:write",
          "audit:read",
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "model:compatibility:check",
          "model:delete",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:manage",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:quota:manage",
          "model:read",
          "model:registry:read",
          "model:registry:write",
          "model:remove",
          "model:unpin",
          "model:write",
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select",
          "scheduler:execute",
          "scheduler:read",
          "scheduler:write",
          "security:read",
          "security:write",
          "training:delete",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      },
      super_admin: {
        description: "Highest privilege role with unrestricted access",
        inherits_from: "admin",
        permissions: [
          "admin:read",
          "admin:system",
          "admin:write",
          "audit:read",
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "model:compatibility:check",
          "model:delete",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:manage",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:quota:manage",
          "model:read",
          "model:registry:read",
          "model:registry:write",
          "model:remove",
          "model:unpin",
          "model:write",
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select",
          "scheduler:execute",
          "scheduler:read",
          "scheduler:write",
          "security:evil_mode",
          "security:read",
          "security:write",
          "training:delete",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      }
    };
    
    const computed: Record<string, Permission[]> = {};
    const roleNames = Object.keys(roles);
    
    // Safety check: if roleNames is empty, initialize with empty permissions
    if (!roleNames || roleNames.length === 0) {
      console.error('[rbac] No role names found in initializeRolePermissions. Initializing with empty permissions.');
      rolePermissionsCache = {};
      return;
    }
    
    for (const roleName of roleNames) {
      try {
        // Safety check: if roleName is undefined, skip
        if (!roleName) {
          console.error('[rbac] Role name is undefined in initializeRolePermissions. Skipping.');
          continue;
        }
        
        computed[roleName] = resolveRolePermissions(roleName);
      } catch (error) {
        console.error(`[rbac] Error resolving permissions for role "${roleName}":`, error);
        computed[roleName] = []; // Initialize with empty permissions on error
      }
    }
    rolePermissionsCache = computed;
  } catch (error) {
    console.error('[rbac] Error in initializeRolePermissions:', error);
    rolePermissionsCache = {};
  }
}

// Function-based API to get role permissions (prevents any module-level initialization)
export const getRolePermissions = (role: UserRole | string | undefined | null): Permission[] => {
  // Return empty array if role is not provided or invalid
  if (!role || typeof role !== 'string') {
    console.warn('[rbac] Invalid or missing role provided to getRolePermissions');
    return [];
  }
  try {
    console.log(`[DEBUG] getRolePermissions called with role: ${role}`);
    
    initializeRolePermissions();
    
    // Check if role exists in the cache
    if (!rolePermissionsCache || !rolePermissionsCache[role]) {
      console.warn(`[rbac] No permissions found for role: ${role}`);
      return [];
    }
    
    console.log(`[DEBUG] rolePermissionsCache keys: ${Object.keys(rolePermissionsCache || {})}`);
    
    const result = rolePermissionsCache ? (rolePermissionsCache[role] || []) : [];
    console.log(`[DEBUG] getRolePermissions returning for role ${role}:`, result);
    return result;
  } catch (error) {
    console.error(`[rbac] Error in getRolePermissions for role "${role}":`, error);
    return [];
  }
}

const ROLE_PERMISSIONS_PROXY = new Proxy({} as Record<string, Permission[]>, {
  get(_target, prop: string | symbol) {
    if (typeof prop !== 'string') {
      return undefined;
    }
    return getRolePermissions(prop);
  },
  ownKeys() {
    // Use the same local copy of roles as in resolveRolePermissions
    const roles = {
      user: {
        description: "Standard platform user",
        inherits_from: null,
        permissions: [
          "data:read",
          "model:info",
          "model:read",
          "training:read",
          "training_data:read"
        ]
      },
      readonly: {
        description: "Read only visibility",
        inherits_from: null,
        permissions: [
          "model:info",
          "model:read",
          "training:read"
        ]
      },
      analyst: {
        description: "Read focused analyst role",
        inherits_from: null,
        permissions: [
          "audit:read",
          "data:export",
          "data:read",
          "model:info",
          "model:read",
          "scheduler:read",
          "training:read",
          "training_data:read"
        ]
      },
      routing_auditor: {
        description: "Read only routing insights",
        inherits_from: null,
        permissions: [
          "routing:audit",
          "routing:health",
          "routing:profile:view"
        ]
      },
      routing_operator: {
        description: "Operational routing control",
        inherits_from: null,
        permissions: [
          "routing:dry_run",
          "routing:health",
          "routing:profile:view",
          "routing:select"
        ]
      },
      routing_admin: {
        description: "Full routing administration",
        inherits_from: null,
        permissions: [
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select"
        ]
      },
      data_steward: {
        description: "Manage datasets and training corpora",
        inherits_from: null,
        permissions: [
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      },
      model_manager: {
        description: "Operational model management",
        inherits_from: null,
        permissions: [
          "model:compatibility:check",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:read",
          "model:remove",
          "model:unpin",
          "model:write"
        ]
      },
      trainer: {
        description: "Training specialist with model and data management access",
        inherits_from: null,
        permissions: [
          "data:export",
          "data:read",
          "data:write",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:info",
          "model:read",
          "model:write",
          "scheduler:read",
          "scheduler:write",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:read",
          "training_data:write"
        ]
      },
      admin: {
        description: "Platform administrator",
        inherits_from: null,
        permissions: [
          "admin:read",
          "admin:system",
          "admin:write",
          "audit:read",
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "model:compatibility:check",
          "model:delete",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:manage",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:quota:manage",
          "model:read",
          "model:registry:read",
          "model:registry:write",
          "model:remove",
          "model:unpin",
          "model:write",
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select",
          "scheduler:execute",
          "scheduler:read",
          "scheduler:write",
          "security:read",
          "security:write",
          "training:delete",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      },
      super_admin: {
        description: "Highest privilege role with unrestricted access",
        inherits_from: "admin",
        permissions: [
          "admin:read",
          "admin:system",
          "admin:write",
          "audit:read",
          "data:delete",
          "data:export",
          "data:read",
          "data:write",
          "model:compatibility:check",
          "model:delete",
          "model:deploy",
          "model:download",
          "model:ensure",
          "model:gc",
          "model:health:check",
          "model:info",
          "model:license:accept",
          "model:license:manage",
          "model:license:view",
          "model:list",
          "model:pin",
          "model:quota:manage",
          "model:read",
          "model:registry:read",
          "model:registry:write",
          "model:remove",
          "model:unpin",
          "model:write",
          "routing:audit",
          "routing:dry_run",
          "routing:health",
          "routing:profile:manage",
          "routing:profile:view",
          "routing:select",
          "scheduler:execute",
          "scheduler:read",
          "scheduler:write",
          "security:evil_mode",
          "security:read",
          "security:write",
          "training:delete",
          "training:execute",
          "training:read",
          "training:write",
          "training_data:delete",
          "training_data:read",
          "training_data:write"
        ]
      }
    };
    
    if (!roles) {
      return [];
    }
    return Object.keys(roles);
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

  // Safety check: if config is undefined, log error and return
  if (!config) {
    console.error('[rbac] Config is undefined in auditPermissionConfig.');
    return;
  }

  const canonicalPermissions = new Set(config.permissions || []);
  const roles = config.roles || {};
  
  const missingRoles = BASELINE_ROLES.filter((role) => !roles[role]);
  if (missingRoles.length > 0) {
    console.warn(
      '[rbac] Missing baseline roles in permissions config:',
      missingRoles.join(', ')
    );
  }

  for (const [roleName, entry] of Object.entries(roles)) {
    if (!entry) {
      console.warn(`[rbac] Role "${roleName}" has undefined entry.`);
      continue;
    }
    
    if (entry.inherits_from && !roles[entry.inherits_from]) {
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
  guest: 1,
  readonly: 2,
  user: 3,
  analyst: 4,
  routing_auditor: 5,
  routing_operator: 6,
  support_agent: 7,
  data_steward: 8,
  model_manager: 9,
  content_manager: 10,
  trainer: 11,
  security_audit: 12,
  routing_admin: 13,
  data_admin: 14,
  model_admin: 15,
  security_admin: 16,
  system_admin: 17,
  admin: 18,
  super_admin: 19,
} as const;
