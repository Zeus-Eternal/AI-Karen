// apps/web/src/services/extensions/permissions.ts
// Permission utility functions for extension management (null-safe, typed, prod-ready)

import type { ExtensionPermissions } from "../../extensions/types";

/** ---------- Types ---------- */
export type RiskLevel = "low" | "medium" | "high";

/** ---------- Permission categories with descriptions ---------- */
export const PERMISSION_CATEGORIES = {
  filesystem: {
    name: "File System",
    description: "Access to read and write files",
    icon: "FolderOpen",
    risk: "medium" as const,
  },
  network: {
    name: "Network",
    description: "Access to make network requests",
    icon: "Globe",
    risk: "high" as const,
  },
  system: {
    name: "System",
    description: "Access to system information and processes",
    icon: "Settings",
    risk: "high" as const,
  },
  data: {
    name: "Data",
    description: "Access to user data and settings",
    icon: "Database",
    risk: "medium" as const,
  },
} as const;

type PermissionCategoryKey = keyof typeof PERMISSION_CATEGORIES;

/** ---------- Specific permission definitions ---------- */
export const PERMISSION_DEFINITIONS = {
  // Filesystem
  "filesystem.read": {
    name: "Read Files",
    description: "Read files from specified directories",
    risk: "low" as const,
  },
  "filesystem.write": {
    name: "Write Files",
    description: "Create and modify files in specified directories",
    risk: "medium" as const,
  },
  "filesystem.delete": {
    name: "Delete Files",
    description: "Delete files from specified directories",
    risk: "high" as const,
  },

  // Network
  "network.http": {
    name: "HTTP Requests",
    description: "Make HTTP/HTTPS requests to external services",
    risk: "medium" as const,
  },
  "network.websocket": {
    name: "WebSocket Connections",
    description: "Establish WebSocket connections",
    risk: "medium" as const,
  },
  "network.unrestricted": {
    name: "Unrestricted Network",
    description: "Make requests to any network endpoint",
    risk: "high" as const,
  },

  // System
  "system.info": {
    name: "System Information",
    description: "Access system information like OS, CPU, memory",
    risk: "low" as const,
  },
  "system.metrics": {
    name: "System Metrics",
    description: "Access real-time system performance metrics",
    risk: "low" as const,
  },
  "system.process": {
    name: "Process Management",
    description: "Start, stop, and manage system processes",
    risk: "high" as const,
  },
  "system.env": {
    name: "Environment Variables",
    description: "Read and modify environment variables",
    risk: "high" as const,
  },

  // Data
  "data.user.read": {
    name: "Read User Data",
    description: "Read user profile and preferences",
    risk: "medium" as const,
  },
  "data.user.write": {
    name: "Write User Data",
    description: "Modify user profile and preferences",
    risk: "high" as const,
  },
  "data.conversations.read": {
    name: "Read Conversations",
    description: "Access chat history and conversations",
    risk: "high" as const,
  },
  "data.conversations.write": {
    name: "Write Conversations",
    description: "Create and modify conversations",
    risk: "high" as const,
  },
  "data.memory.read": {
    name: "Read Memory",
    description: "Access AI memory and knowledge base",
    risk: "medium" as const,
  },
  "data.memory.write": {
    name: "Write Memory",
    description: "Modify AI memory and knowledge base",
    risk: "high" as const,
  },
} as const;

type KnownPermissionKey = keyof typeof PERMISSION_DEFINITIONS;

/** ---------- Helpers ---------- */
const safeArr = (v: unknown): string[] => (Array.isArray(v) ? (v as string[]) : []);
const uniq = (arr: string[]) => Array.from(new Set(arr));
const isKnownPerm = (p: string): p is KnownPermissionKey => p in PERMISSION_DEFINITIONS;

/** ---------- API ---------- */

/** Gets permission display information, with graceful fallback */
export function getPermissionInfo(permission: string) {
  if (isKnownPerm(permission)) return PERMISSION_DEFINITIONS[permission];
  return {
    name: permission,
    description: "Custom permission",
    risk: "medium" as const,
  };
}

/** Groups permissions by category (always returns all categories, even if empty) */
export function groupPermissionsByCategory(
  permissions: ExtensionPermissions
): Record<PermissionCategoryKey, string[]> {
  const grouped: Record<PermissionCategoryKey, string[]> = {
    filesystem: [],
    network: [],
    system: [],
    data: [],
  };

  if (permissions?.filesystem) grouped.filesystem = [...permissions.filesystem];
  if (permissions?.network) grouped.network = [...permissions.network];
  if (permissions?.system) grouped.system = [...permissions.system];
  if (permissions?.data) grouped.data = [...permissions.data];

  return grouped;
}

/** Calculates overall risk level for a permission set */
export function calculatePermissionRisk(
  permissions: ExtensionPermissions
): RiskLevel {
  let riskScore = 0;
  let total = 0;

  const allPermissions = [
    ...safeArr(permissions?.filesystem),
    ...safeArr(permissions?.network),
    ...safeArr(permissions?.system),
    ...safeArr(permissions?.data),
  ];

  for (const perm of allPermissions) {
    const info = getPermissionInfo(perm);
    total++;
    switch (info.risk) {
      case "low":
        riskScore += 1;
        break;
      case "medium":
        riskScore += 2;
        break;
      case "high":
        riskScore += 3;
        break;
    }
  }

  if (total === 0) return "low";
  const avg = riskScore / total;

  if (avg <= 1.5) return "low";
  if (avg <= 2.5) return "medium";
  return "high";
}

/** Tailwind-ish color classes for risk */
export function getRiskColorClass(risk: RiskLevel): string {
  const colorMap: Record<RiskLevel, string> = {
    low: "text-green-600 bg-green-50 border-green-200",
    medium: "text-yellow-600 bg-yellow-50 border-yellow-200",
    high: "text-red-600 bg-red-50 border-red-200",
  };
  return colorMap[risk];
}

/** Checks if user has granted a specific permission within a category */
export function hasPermission(
  granted: ExtensionPermissions,
  requiredPermission: string,
  category: keyof ExtensionPermissions
): boolean {
  const list = safeArr(granted?.[category]);
  return list.includes(requiredPermission);
}

/** Checks if all required permissions are granted */
export function hasAllPermissions(
  granted: ExtensionPermissions,
  required: ExtensionPermissions
): boolean {
  const categories: (keyof ExtensionPermissions)[] = [
    "filesystem",
    "network",
    "system",
    "data",
  ];
  for (const cat of categories) {
    const reqList = safeArr(required?.[cat]);
    for (const p of reqList) {
      if (!hasPermission(granted, p, cat)) return false;
    }
  }
  return true;
}

/** Returns the missing permissions (by category) */
export function getMissingPermissions(
  granted: ExtensionPermissions,
  required: ExtensionPermissions
): ExtensionPermissions {
  return {
    filesystem: safeArr(required.filesystem).filter((p) =>
      !hasPermission(granted, p, "filesystem")
    ),
    network: safeArr(required.network).filter((p) =>
      !hasPermission(granted, p, "network")
    ),
    system: safeArr(required.system).filter((p) =>
      !hasPermission(granted, p, "system")
    ),
    data: safeArr(required.data).filter((p) =>
      !hasPermission(granted, p, "data")
    ),
  };
}

/** Formats permission set for display by category */
export function formatPermissionsForDisplay(permissions: ExtensionPermissions): {
  category: string;
  permissions: Array<{ name: string; description: string; risk: RiskLevel }>;
}[] {
  const grouped = groupPermissionsByCategory(permissions);

  return (Object.keys(grouped) as PermissionCategoryKey[])
    .filter((cat) => grouped[cat].length > 0)
    .map((cat) => ({
      category: PERMISSION_CATEGORIES[cat].name,
      permissions: grouped[cat].map((perm) => getPermissionInfo(perm)),
    }));
}

/** Creates a permission request object with computed risk */
export function createPermissionRequest(
  extensionId: string,
  permissions: ExtensionPermissions,
  reason?: string
): {
  extensionId: string;
  permissions: ExtensionPermissions;
  reason?: string;
  risk: RiskLevel;
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

/** Validates structure of a permission request */
export function validatePermissionRequest(request: any): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!request?.extensionId) errors.push("Extension ID is required");

  if (!request?.permissions || typeof request.permissions !== "object") {
    errors.push("Permissions object is required");
  } else {
    for (const [category, perms] of Object.entries(request.permissions)) {
      if (!(category in PERMISSION_CATEGORIES)) {
        errors.push(`Invalid permission category: ${category}`);
        continue;
      }
      if (!Array.isArray(perms)) {
        errors.push(`Permissions for ${category} must be an array`);
        continue;
      }
      for (const perm of perms as unknown[]) {
        if (typeof perm !== "string") {
          errors.push(`Permission must be a string: ${String(perm)}`);
        }
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

/** Merges multiple permission sets (unique per category) */
export function mergePermissions(
  ...permissionSets: ExtensionPermissions[]
): ExtensionPermissions {
  const merged: ExtensionPermissions = {
    filesystem: [],
    network: [],
    system: [],
    data: [],
  };

  for (const set of permissionSets) {
    if (set?.filesystem)
      merged.filesystem = uniq([...merged.filesystem!, ...set.filesystem]);
    if (set?.network)
      merged.network = uniq([...merged.network!, ...set.network]);
    if (set?.system) merged.system = uniq([...merged.system!, ...set.system]);
    if (set?.data) merged.data = uniq([...merged.data!, ...set.data]);
  }

  return merged;
}

/** Removes permissions from a base set */
export function removePermissions(
  base: ExtensionPermissions,
  toRemove: ExtensionPermissions
): ExtensionPermissions {
  return {
    filesystem: safeArr(base.filesystem).filter(
      (p) => !safeArr(toRemove.filesystem).includes(p)
    ),
    network: safeArr(base.network).filter(
      (p) => !safeArr(toRemove.network).includes(p)
    ),
    system: safeArr(base.system).filter(
      (p) => !safeArr(toRemove.system).includes(p)
    ),
    data: safeArr(base.data).filter(
      (p) => !safeArr(toRemove.data).includes(p)
    ),
  };
}
