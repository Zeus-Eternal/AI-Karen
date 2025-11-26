/**
 * Shared RBAC utilities for components
 * 
 * This module contains shared utilities for working with RBAC permissions
 * across different components in the application.
 */

/**
 * Normalize a permission string to a canonical format
 * @param permission The permission string to normalize
 * @returns The normalized permission string, or null if invalid
 */
export function normalizePermission(permission: string): string | null {
  if (!permission || typeof permission !== 'string') {
    return null;
  }
  
  // Convert to lowercase and trim whitespace
  const normalized = permission.toLowerCase().trim();
  
  // Basic validation - ensure it contains at least one colon
  if (!normalized.includes(':')) {
    return null;
  }
  
  // Split into parts and validate each part
  const parts = normalized.split(':');
  
  // Ensure we have at least 2 parts (e.g., 'admin:read')
  if (parts.length < 2) {
    return null;
  }
  
  // Filter out empty parts and join back with colons
  const validParts = parts.filter(part => part.length > 0);
  if (validParts.length < 2) {
    return null;
  }
  
  return validParts.join(':');
}

/**
 * Normalize a list of permissions
 * @param permissions Array of permission strings to normalize
 * @returns Array of normalized permission strings
 */
export function normalizePermissionList(permissions: string[]): string[] {
  if (!Array.isArray(permissions)) {
    return [];
  }
  
  const normalizedPermissions: string[] = [];
  
  for (const permission of permissions) {
    const normalized = normalizePermission(permission);
    if (normalized) {
      normalizedPermissions.push(normalized);
    }
  }
  
  // Return unique permissions
  return [...new Set(normalizedPermissions)];
}

/**
 * Check if a permission string matches a pattern
 * @param permission The permission to check
 * @param pattern The pattern to match against (can use * as wildcard)
 * @returns True if the permission matches the pattern
 */
export function permissionMatchesPattern(permission: string, pattern: string): boolean {
  if (!permission || !pattern) {
    return false;
  }
  
  // Convert to regex pattern
  const regexPattern = pattern
    .replace(/\*/g, '.*')  // Replace * with .*
    .replace(/[.+?^${}()|[\]\\]/g, '\\$&'); // Escape regex special chars except *
  
  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(permission);
}

/**
 * Check if a permission implies another permission
 * @param sourcePermission The source permission
 * @param targetPermission The target permission to check
 * @returns True if sourcePermission implies targetPermission
 */
export function permissionImplies(sourcePermission: string, targetPermission: string): boolean {
  if (!sourcePermission || !targetPermission) {
    return false;
  }
  
  // Exact match
  if (sourcePermission === targetPermission) {
    return true;
  }
  
  // Wildcard matching
  if (sourcePermission.includes('*')) {
    return permissionMatchesPattern(targetPermission, sourcePermission);
  }
  
  // Hierarchical matching (e.g., 'admin:*' implies 'admin:read')
  const sourceParts = sourcePermission.split(':');
  const targetParts = targetPermission.split(':');
  
  // If source has fewer parts, it can't imply a target with more parts
  if (sourceParts.length > targetParts.length) {
    return false;
  }
  
  // Check each part
  for (let i = 0; i < sourceParts.length; i++) {
    const sourcePart = sourceParts[i];
    const targetPart = targetParts[i];
    
    // Wildcard matches anything
    if (sourcePart === '*') {
      continue;
    }
    
    // Exact match required
    if (sourcePart !== targetPart) {
      return false;
    }
  }
  
  return true;
}

/**
 * Extract the category from a permission string
 * @param permission The permission string
 * @returns The category part of the permission, or null if invalid
 */
export function getPermissionCategory(permission: string): string | null {
  const normalized = normalizePermission(permission);
  if (!normalized) {
    return null;
  }
  
  const parts = normalized.split(':');
  return parts[0] || null;
}

/**
 * Extract the action from a permission string
 * @param permission The permission string
 * @returns The action part of the permission, or null if invalid
 */
export function getPermissionAction(permission: string): string | null {
  const normalized = normalizePermission(permission);
  if (!normalized) {
    return null;
  }
  
  const parts = normalized.split(':');
  return parts[1] || null;
}

/**
 * Check if a permission is a wildcard permission
 * @param permission The permission string
 * @returns True if the permission contains wildcards
 */
export function isWildcardPermission(permission: string): boolean {
  if (!permission) {
    return false;
  }
  
  return permission.includes('*');
}

/**
 * Get all implied permissions for a given permission
 * @param permission The base permission
 * @returns Array of all implied permissions
 */
export function getImpliedPermissions(permission: string): string[] {
  const normalized = normalizePermission(permission);
  if (!normalized) {
    return [];
  }
  
  const implied: string[] = [normalized];
  
  // If it's already a wildcard, no additional implications
  if (isWildcardPermission(normalized)) {
    return implied;
  }
  
  const parts = normalized.split(':');
  
  // Add wildcard variants for each part
  for (let i = 1; i < parts.length; i++) {
    const wildcardParts = [...parts];
    wildcardParts[i] = '*';
    const wildcardPermission = wildcardParts.slice(0, i + 1).join(':');
    implied.push(wildcardPermission);
  }
  
  return [...new Set(implied)];
}