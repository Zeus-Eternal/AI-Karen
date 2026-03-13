/**
 * RBAC (Role-Based Access Control) Types
 * Defines types for role-based access control system
 */

export enum RoleName {
  ADMIN = 'admin',
  MODERATOR = 'moderator', 
  USER = 'user',
  GUEST = 'guest',
  DEVELOPER = 'developer',
  SYSTEM = 'system'
}

export enum Permission {
  // User permissions
  READ_MESSAGES = 'read_messages',
  WRITE_MESSAGES = 'write_messages',
  DELETE_MESSAGES = 'delete_messages',
  
  // Conversation permissions
  CREATE_CONVERSATION = 'create_conversation',
  READ_CONVERSATION = 'read_conversation',
  UPDATE_CONVERSATION = 'update_conversation',
  DELETE_CONVERSATION = 'delete_conversation',
  
  // System permissions
  MANAGE_USERS = 'manage_users',
  MANAGE_ROLES = 'manage_roles',
  MANAGE_PERMISSIONS = 'manage_permissions',
  VIEW_LOGS = 'view_logs',
  
  // AI/Model permissions
  USE_AI_MODELS = 'use_ai_models',
  MANAGE_MODELS = 'manage_models',
  CONFIGURE_MODELS = 'configure_models',
  
  // Security permissions
  VIEW_SECURITY_LOGS = 'view_security_logs',
  MANAGE_SECURITY = 'manage_security',
  CONFIGURE_SECURITY = 'configure_security',
  
  // Administrative permissions
  SYSTEM_ADMIN = 'system_admin',
  BACKUP_RESTORE = 'backup_restore',
  CONFIGURE_SYSTEM = 'configure_system'
}

export interface Role {
  id: string;
  name: RoleName;
  description: string;
  permissions: Permission[];
  isSystem: boolean;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, unknown>;
}

export interface UserRole {
  userId: string;
  roleId: string;
  assignedAt: string;
  assignedBy: string;
  expiresAt?: string;
  isActive: boolean;
  metadata?: Record<string, unknown>;
}

export interface PermissionCheck {
  permission: Permission;
  granted: boolean;
  reason?: string;
  checkedAt: string;
  context?: Record<string, unknown>;
}

export interface AccessContext {
  userId: string;
  userRole: RoleName;
  permissions: Permission[];
  sessionId: string;
  operation?: string;
  resource?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface RBACPolicy {
  id: string;
  name: string;
  description: string;
  rules: RBACRule[];
  isActive: boolean;
  priority: number;
  createdAt: string;
  updatedAt: string;
}

export interface RBACRule {
  id: string;
  condition: string;
  effect: string;
  permissions: Permission[];
  roles?: RoleName[];
  priority: number;
  isActive: boolean;
}

export interface AccessDecision {
  allowed: boolean;
  reason?: string;
  requiredPermissions?: Permission[];
  missingPermissions?: Permission[];
  evaluatedAt: string;
  context?: AccessContext;
  policy?: RBACPolicy;
}

export interface RoleHierarchy {
  role: RoleName;
  level: number;
  inherits?: RoleName[];
  canAssign?: RoleName[];
  canBeAssignedBy?: RoleName[];
}

export const ROLE_HIERARCHY: RoleHierarchy[] = [
  { role: RoleName.GUEST, level: 0, canAssign: [RoleName.GUEST], canBeAssignedBy: [RoleName.USER, RoleName.MODERATOR, RoleName.ADMIN, RoleName.DEVELOPER] },
  { role: RoleName.USER, level: 1, inherits: [RoleName.GUEST], canAssign: [RoleName.USER], canBeAssignedBy: [RoleName.MODERATOR, RoleName.ADMIN, RoleName.DEVELOPER] },
  { role: RoleName.MODERATOR, level: 2, inherits: [RoleName.USER], canAssign: [RoleName.USER], canBeAssignedBy: [RoleName.ADMIN, RoleName.DEVELOPER] },
  { role: RoleName.DEVELOPER, level: 3, inherits: [RoleName.USER], canAssign: [RoleName.USER], canBeAssignedBy: [RoleName.ADMIN] },
  { role: RoleName.ADMIN, level: 4, inherits: [RoleName.MODERATOR, RoleName.USER], canAssign: [RoleName.GUEST, RoleName.USER, RoleName.MODERATOR, RoleName.DEVELOPER] },
  { role: RoleName.SYSTEM, level: 5, inherits: [], canAssign: [], canBeAssignedBy: [] }
];

// Define base permissions for each role
const USER_PERMISSIONS: Permission[] = [
  Permission.READ_MESSAGES,
  Permission.WRITE_MESSAGES,
  Permission.DELETE_MESSAGES,
  Permission.CREATE_CONVERSATION,
  Permission.READ_CONVERSATION,
  Permission.UPDATE_CONVERSATION,
  Permission.DELETE_CONVERSATION,
  Permission.USE_AI_MODELS
];

const MODERATOR_PERMISSIONS: Permission[] = [
  ...USER_PERMISSIONS,
  Permission.MANAGE_USERS,
  Permission.VIEW_LOGS
];

const ADMIN_PERMISSIONS: Permission[] = [
  ...MODERATOR_PERMISSIONS,
  Permission.MANAGE_ROLES,
  Permission.MANAGE_PERMISSIONS,
  Permission.MANAGE_MODELS,
  Permission.CONFIGURE_MODELS,
  Permission.VIEW_SECURITY_LOGS,
  Permission.MANAGE_SECURITY,
  Permission.CONFIGURE_SECURITY
];

const DEVELOPER_PERMISSIONS: Permission[] = [
  ...ADMIN_PERMISSIONS,
  Permission.CONFIGURE_SYSTEM
];

const SYSTEM_PERMISSIONS: Permission[] = [
  Permission.SYSTEM_ADMIN,
  Permission.BACKUP_RESTORE,
  Permission.CONFIGURE_SYSTEM
];

export const PERMISSION_GROUPS: Record<RoleName, Permission[]> = {
  [RoleName.USER]: USER_PERMISSIONS,
  [RoleName.MODERATOR]: MODERATOR_PERMISSIONS,
  [RoleName.ADMIN]: ADMIN_PERMISSIONS,
  [RoleName.DEVELOPER]: DEVELOPER_PERMISSIONS,
  [RoleName.GUEST]: [],
  [RoleName.SYSTEM]: SYSTEM_PERMISSIONS
};

export function hasPermission(userRole: RoleName, permission: Permission): boolean {
  const roleHierarchy = ROLE_HIERARCHY.find(h => h.role === userRole);
  if (!roleHierarchy) return false;
  
  const roleIndex = Object.values(RoleName).indexOf(userRole);
  const permissionGroups = Object.values(PERMISSION_GROUPS) as Permission[][];
  const userPermissions = roleIndex >= 0 && roleIndex < permissionGroups.length ? permissionGroups[roleIndex] : [];
  
  return roleHierarchy.level >= ROLE_HIERARCHY.find(h => h.role === RoleName.ADMIN)!.level &&
         (userPermissions || []).includes(permission);
}

export function canAssignRole(assignerRole: RoleName, targetRole: RoleName): boolean {
  const assignerHierarchy = ROLE_HIERARCHY.find(h => h.role === assignerRole);
  const targetHierarchy = ROLE_HIERARCHY.find(h => h.role === targetRole);
  
  if (!assignerHierarchy || !targetHierarchy) return false;
  
  return assignerHierarchy.level >= targetHierarchy.level &&
         (targetHierarchy.canBeAssignedBy || []).includes(assignerRole) || false;
}

export function getRolePermissions(roleName: RoleName): Permission[] {
  return PERMISSION_GROUPS[roleName] || [];
}

export function validateAccess(context: AccessContext, requiredPermissions: Permission[]): AccessDecision {
  const userPermissions = getRolePermissions(context.userRole);
  const missingPermissions = requiredPermissions.filter(p => !userPermissions.includes(p));
  
  return {
    allowed: missingPermissions.length === 0,
    reason: missingPermissions.length > 0 ? `Missing permissions: ${missingPermissions.join(', ')}` : undefined,
    missingPermissions,
    requiredPermissions,
    evaluatedAt: context.timestamp,
    context
  };
}