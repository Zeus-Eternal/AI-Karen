// Permission utility functions for extension management

import type { ExtensionPermissions } from '../../extensions/types';

/**
 * Permission categories with descriptions
 */
export const PERMISSION_CATEGORIES = {
  filesystem: {
    name: 'File System',
    description: 'Access to read and write files',
    icon: 'FolderOpen',
    risk: 'medium' as const,
  },
  network: {
    name: 'Network',
    description: 'Access to make network requests',
    icon: 'Globe',
    risk: 'high' as const,
  },
  system: {
    name: 'System',
    description: 'Access to system information and processes',
    icon: 'Settings',
    risk: 'high' as const,
  },
  data: {
    name: 'Data',
    description: 'Access to user data and settings',
    icon: 'Database',
    risk: 'medium' as const,
  },
} as const;

/**
 * Specific permission definitions
 */
export const PERMISSION_DEFINITIONS = {
  // Filesystem permissions
  'filesystem.read': {
    name: 'Read Files',
    description: 'Read files from specified directories',
    risk: 'low' as const,
  },
  'filesystem.write': {
    name: 'Write Files',
    description: 'Create and modify files in specified directories',
    risk: 'medium' as const,
  },
  'filesystem.delete': {
    name: 'Delete Files',
    description: 'Delete files from specified directories',
    risk: 'high' as const,
  },
  
  // Network permissions
  'network.http': {
    name: 'HTTP Requests',
    description: 'Make HTTP/HTTPS requests to external services',
    risk: 'medium' as const,
  },
  'network.websocket': {
    name: 'WebSocket Connections',
    description: 'Establish WebSocket connections',
    risk: 'medium' as const,
  },
  'network.unrestricted': {
    name: 'Unrestricted Network',
    description: 'Make requests to any network endpoint',
    risk: 'high' as const,
  },
  
  // System permissions
  'system.info': {
    name: 'System Information',
    description: 'Access system information like OS, CPU, memory',
    risk: 'low' as const,
  },
  'system.metrics': {
    name: 'System Metrics',
    description: 'Access real-time system performance metrics',
    risk: 'low' as const,
  },
  'system.process': {
    name: 'Process Management',
    description: 'Start, stop, and manage system processes',
    risk: 'high' as const,
  },
  'system.env': {
    name: 'Environment Variables',
    description: 'Read and modify environment variables',
    risk: 'high' as const,
  },
  
  // Data permissions
  'data.user.read': {
    name: 'Read User Data',
    description: 'Read user profile and preferences',
    risk: 'medium' as const,
  },
  'data.user.write': {
    name: 'Write User Data',
    description: 'Modify user profile and preferences',
    risk: 'high' as const,
  },
  'data.conversations.read': {
    name: 'Read Conversations',
    description: 'Access chat history and conversations',
    risk: 'high' as const,
  },
  'data.conversations.write': {
    name: 'Write Conversations',
    description: 'Create and modify conversations',
    risk: 'high' as const,
  },
  'data.memory.read': {
    name: 'Read Memory',
    description: 'Access AI memory and knowledge base',
    risk: 'medium' as const,
  },
  'data.memory.write': {
    name: 'Write Memory',
    description: 'Modify AI memory and knowledge base',
    risk: 'high' as const,
  },
} as const;

/**
 * Gets permission display information
 */
export function getPermissionInfo(permission: string) {
  return PERMISSION_DEFINITIONS[permission as keyof typeof PERMISSION_DEFINITIONS] || {
    name: permission,
    description: 'Custom permission',
    risk: 'medium' as const,
  };
}

/**
 * Groups permissions by category
 */
export function groupPermissionsByCategory(permissions: ExtensionPermissions): Record<string, string[]> {
  const grouped: Record<string, string[]> = {};
  
  // Initialize categories
  Object.keys(PERMISSION_CATEGORIES).forEach(category => {
    grouped[category] = [];
  });
  
  // Group filesystem permissions
  if (permissions.filesystem) {
    grouped.filesystem = permissions.filesystem;
  }
  
  // Group network permissions
  if (permissions.network) {
    grouped.network = permissions.network;
  }
  
  // Group system permissions
  if (permissions.system) {
    grouped.system = permissions.system;
  }
  
  // Group data permissions
  if (permissions.data) {
    grouped.data = permissions.data;
  }
  
  return grouped;
}

/**
 * Calculates overall risk level for permissions
 */
export function calculatePermissionRisk(permissions: ExtensionPermissions): 'low' | 'medium' | 'high' {
  let riskScore = 0;
  let totalPermissions = 0;
  
  const allPermissions = [
    ...(permissions.filesystem || []),
    ...(permissions.network || []),
    ...(permissions.system || []),
    ...(permissions.data || []),
  ];
  
  for (const permission of allPermissions) {
    const info = getPermissionInfo(permission);
    totalPermissions++;
    
    switch (info.risk) {
      case 'low':
        riskScore += 1;
        break;
      case 'medium':
        riskScore += 2;
        break;
      case 'high':
        riskScore += 3;
        break;
    }
  }
  
  if (totalPermissions === 0) return 'low';
  
  const averageRisk = riskScore / totalPermissions;
  
  if (averageRisk <= 1.5) return 'low';
  if (averageRisk <= 2.5) return 'medium';
  return 'high';
}

/**
 * Gets risk color class for UI
 */
export function getRiskColorClass(risk: 'low' | 'medium' | 'high'): string {
  const colorMap = {
    low: 'text-green-600 bg-green-50 border-green-200',
    medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    high: 'text-red-600 bg-red-50 border-red-200',
  };
  
  return colorMap[risk];
}

/**
 * Checks if user has granted specific permission
 */
export function hasPermission(
  grantedPermissions: ExtensionPermissions,
  requiredPermission: string,
  category: keyof ExtensionPermissions
): boolean {
  const categoryPermissions = grantedPermissions[category] || [];
  return categoryPermissions.includes(requiredPermission);
}

/**
 * Checks if all required permissions are granted
 */
export function hasAllPermissions(
  grantedPermissions: ExtensionPermissions,
  requiredPermissions: ExtensionPermissions
): boolean {
  // Check filesystem permissions
  if (requiredPermissions.filesystem) {
    for (const perm of requiredPermissions.filesystem) {
      if (!hasPermission(grantedPermissions, perm, 'filesystem')) {
        return false;
      }
    }
  }
  
  // Check network permissions
  if (requiredPermissions.network) {
    for (const perm of requiredPermissions.network) {
      if (!hasPermission(grantedPermissions, perm, 'network')) {
        return false;
      }
    }
  }
  
  // Check system permissions
  if (requiredPermissions.system) {
    for (const perm of requiredPermissions.system) {
      if (!hasPermission(grantedPermissions, perm, 'system')) {
        return false;
      }
    }
  }
  
  // Check data permissions
  if (requiredPermissions.data) {
    for (const perm of requiredPermissions.data) {
      if (!hasPermission(grantedPermissions, perm, 'data')) {
        return false;
      }
    }
  }
  
  return true;
}

/**
 * Gets missing permissions
 */
export function getMissingPermissions(
  grantedPermissions: ExtensionPermissions,
  requiredPermissions: ExtensionPermissions
): ExtensionPermissions {
  const missing: ExtensionPermissions = {
    filesystem: [],
    network: [],
    system: [],
    data: [],
  };
  
  // Check filesystem permissions
  if (requiredPermissions.filesystem) {
    missing.filesystem = requiredPermissions.filesystem.filter(
      perm => !hasPermission(grantedPermissions, perm, 'filesystem')
    );
  }
  
  // Check network permissions
  if (requiredPermissions.network) {
    missing.network = requiredPermissions.network.filter(
      perm => !hasPermission(grantedPermissions, perm, 'network')
    );
  }
  
  // Check system permissions
  if (requiredPermissions.system) {
    missing.system = requiredPermissions.system.filter(
      perm => !hasPermission(grantedPermissions, perm, 'system')
    );
  }
  
  // Check data permissions
  if (requiredPermissions.data) {
    missing.data = requiredPermissions.data.filter(
      perm => !hasPermission(grantedPermissions, perm, 'data')
    );
  }
  
  return missing;
}

/**
 * Formats permissions for display
 */
export function formatPermissionsForDisplay(permissions: ExtensionPermissions): {
  category: string;
  permissions: Array<{
    name: string;
    description: string;
    risk: 'low' | 'medium' | 'high';
  }>;
}[] {
  const grouped = groupPermissionsByCategory(permissions);
  
  return Object.entries(grouped)
    .filter(([, perms]) => perms.length > 0)
    .map(([category, perms]) => ({
      category: PERMISSION_CATEGORIES[category as keyof typeof PERMISSION_CATEGORIES].name,
      permissions: perms.map(perm => getPermissionInfo(perm)),
    }));
}

/**
 * Creates a permission request object
 */
export function createPermissionRequest(
  extensionId: string,
  permissions: ExtensionPermissions,
  reason?: string
): {
  extensionId: string;
  permissions: ExtensionPermissions;
  reason?: string;
  risk: 'low' | 'medium' | 'high';
  timestamp: string;
} {
  return {
    extensionId,
    permissions,
    reason,
    risk: calculatePermissionRisk(permissions),
    timestamp: new Date().toISOString(),
  };
}

/**
 * Validates permission request
 */
export function validatePermissionRequest(request: any): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!request.extensionId) {
    errors.push('Extension ID is required');
  }
  
  if (!request.permissions || typeof request.permissions !== 'object') {
    errors.push('Permissions object is required');
  }
  
  // Validate each permission category
  if (request.permissions) {
    for (const [category, perms] of Object.entries(request.permissions)) {
      if (!PERMISSION_CATEGORIES[category as keyof typeof PERMISSION_CATEGORIES]) {
        errors.push(`Invalid permission category: ${category}`);
        continue;
      }
      
      if (!Array.isArray(perms)) {
        errors.push(`Permissions for ${category} must be an array`);
        continue;
      }
      
      for (const perm of perms as string[]) {
        if (typeof perm !== 'string') {
          errors.push(`Permission must be a string: ${perm}`);
        }
      }
    }
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Merges permission sets
 */
export function mergePermissions(
  ...permissionSets: ExtensionPermissions[]
): ExtensionPermissions {
  const merged: ExtensionPermissions = {
    filesystem: [],
    network: [],
    system: [],
    data: [],
  };
  
  for (const permissions of permissionSets) {
    if (permissions.filesystem) {
      merged.filesystem = [...new Set([...merged.filesystem, ...permissions.filesystem])];
    }
    if (permissions.network) {
      merged.network = [...new Set([...merged.network, ...permissions.network])];
    }
    if (permissions.system) {
      merged.system = [...new Set([...merged.system, ...permissions.system])];
    }
    if (permissions.data) {
      merged.data = [...new Set([...merged.data, ...permissions.data])];
    }
  }
  
  return merged;
}

/**
 * Removes permissions from a set
 */
export function removePermissions(
  basePermissions: ExtensionPermissions,
  toRemove: ExtensionPermissions
): ExtensionPermissions {
  return {
    filesystem: basePermissions.filesystem?.filter(
      perm => !toRemove.filesystem?.includes(perm)
    ) || [],
    network: basePermissions.network?.filter(
      perm => !toRemove.network?.includes(perm)
    ) || [],
    system: basePermissions.system?.filter(
      perm => !toRemove.system?.includes(perm)
    ) || [],
    data: basePermissions.data?.filter(
      perm => !toRemove.data?.includes(perm)
    ) || [],
  };
}