/**
 * Unified Role-Based Access Control (RBAC) System
 *
 * Single source of truth for all role and permission logic.
 * Matches backend role system: super_admin, admin, user
 */

export type UserRole = "super_admin" | "admin" | "user";

export type Permission =
  | "chat.send"
  | "chat.code_assistance"
  | "chat.explanations"
  | "chat.documentation"
  | "chat.analysis"
  | "voice.input"
  | "voice.output"
  | "attachments.upload"
  | "attachments.download"
  | "admin.settings"
  | "admin.users"
  | "admin.create"
  | "admin.edit"
  | "admin.delete"
  | "user.create"
  | "user.edit"
  | "user.delete"
  | "user.view"
  | "system.config"
  | "system.audit"
  | "system.security";

export const ROLE_HIERARCHY: Record<UserRole, number> = {
  user: 1,
  admin: 2,
  super_admin: 3,
} as const;

export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  user: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
  ],
  admin: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "admin.settings",
    "admin.users",
    "user.create",
    "user.edit",
    "user.delete",
    "user.view",
  ],
  super_admin: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "admin.settings",
    "admin.users",
    "admin.create",
    "admin.edit",
    "admin.delete",
    "user.create",
    "user.edit",
    "user.delete",
    "user.view",
    "system.config",
    "system.audit",
    "system.security",
  ],
} as const;

/**
 * Determine highest role from roles array (matches backend logic)
 * Used by: AuthContext, session.ts, test-utils, RBACGuard
 */
export function getHighestRole(roles: readonly string[] | undefined | null): UserRole {
  if (!roles || roles.length === 0) return "user";
  if (roles.includes("super_admin")) return "super_admin";
  if (roles.includes("admin")) return "admin";
  return "user";
}

/**
 * Get role display name
 */
export function getRoleDisplayName(role: UserRole | string): string {
  switch (role) {
    case "super_admin":
      return "Super Admin";
    case "admin":
      return "Admin";
    case "user":
      return "User";
    default:
      return role || "Unknown";
  }
}

/**
 * Check if a role has a specific permission
 */
export function roleHasPermission(role: UserRole, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

/**
 * Check if a role is higher or equal to another role
 */
export function roleHierarchy(userRole: UserRole, requiredRole: UserRole): boolean {
  return ROLE_HIERARCHY[userRole] >= ROLE_HIERARCHY[requiredRole];
}

/**
 * Check if role can manage another role
 * Super admins can manage everyone, admins can manage users
 */
export function canManageRole(managerRole: UserRole, targetRole: UserRole): boolean {
  if (managerRole === "super_admin") return true;
  if (managerRole === "admin") return targetRole === "user";
  return false;
}

/**
 * Validate role string
 */
export function isValidRole(role: string): role is UserRole {
  return ["super_admin", "admin", "user"].includes(role);
}
