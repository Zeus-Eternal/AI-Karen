"use client";

import React, { createContext, useContext, useCallback, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  type AccessContext,
  type EvilModeConfig,
  type EvilModeSession,
  type Permission,
  type PermissionCheckResult,
  type RBACConfig,
  type Role,
  type RoleHierarchy,
  type User,
  type Restriction,
} from "@/types/rbac";
import { enhancedApiClient } from "@/lib/enhanced-api-client";
import { useAppStore, type AppState } from "@/store/app-store";

export interface RBACContextValue {
  // Current user and permissions
  currentUser: User | null;
  userRoles: Role[];
  effectivePermissions: Permission[];
  
  // Permission checking
  hasPermission: (permission: Permission, context?: Partial<AccessContext>) => boolean;
  checkPermission: (permission: Permission, context?: Partial<AccessContext>) => PermissionCheckResult;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  
  // Role management
  getUserRoles: (userId: string) => Promise<Role[]>;
  assignRole: (userId: string, roleId: string) => Promise<void>;
  removeRole: (userId: string, roleId: string) => Promise<void>;
  
  // Evil Mode
  isEvilModeEnabled: boolean;
  canEnableEvilMode: boolean;
  enableEvilMode: (justification: string, additionalAuth?: string) => Promise<void>;
  disableEvilMode: () => Promise<void>;
  evilModeSession: EvilModeSession | null;
  
  // Configuration
  rbacConfig: RBACConfig;
  evilModeConfig: EvilModeConfig;
  
  // Loading states
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

const RBACContext = createContext<RBACContextValue | null>(null);

export interface RBACProviderProps {
  children: React.ReactNode;
  config?: Partial<RBACConfig>;
}

export function RBACProvider({ children, config }: RBACProviderProps) {
  const queryClient = useQueryClient();
  const appUser = useAppStore((state) => state.user);

  const baseConfig = useMemo(() => ({
    ...getDefaultRBACConfig(),
    ...config,
  }), [config]);

  const { data: rbacConfigData = baseConfig } = useQuery<RBACConfig, Error>({
    queryKey: ["rbac", "config"],
    queryFn: async () => {
      const response = await enhancedApiClient.get<RBACConfig>("/api/rbac/config");
      return response.data ?? baseConfig;
    },
    initialData: baseConfig,
    staleTime: 5 * 60 * 1000,
  });

  const rbacConfig = useMemo(
    () => ({
      ...baseConfig,
      ...rbacConfigData,
    }),
    [baseConfig, rbacConfigData]
  );

  const { data: evilModeConfig = getDefaultEvilModeConfig() } = useQuery<EvilModeConfig, Error>({
    queryKey: ["rbac", "evil-mode-config"],
    queryFn: async () => {
      const response = await enhancedApiClient.get<EvilModeConfig>("/api/rbac/evil-mode/config");
      return response.data ?? getDefaultEvilModeConfig();
    },
    initialData: getDefaultEvilModeConfig(),
    staleTime: 5 * 60 * 1000,
  });

  const { data: currentUser = null } = useQuery<User | null, Error>({
    queryKey: ["rbac", "current-user", appUser?.id],
    queryFn: async () => {
      const storeUser = appUser;

      if (!storeUser?.id) {
        return null;
      }

      const response = await enhancedApiClient.get<User>(`/api/rbac/users/${storeUser.id}`);
      return response.data ?? mapStoreUserToRBACUser(storeUser);
    },
    enabled: Boolean(appUser?.id),
    initialData: () => (appUser ? mapStoreUserToRBACUser(appUser) : null),
    staleTime: 2 * 60 * 1000,
  });

  const {
    data: userRoles = [],
    isLoading: rolesLoading,
    isError: rolesError,
    error: rolesErrorData,
  } = useQuery<Role[], Error>({
    queryKey: ["rbac", "user-roles", currentUser?.id],
    queryFn: async () => {
      if (!currentUser?.id) {
        return [];
      }

      const response = await enhancedApiClient.get<Role[]>(`/api/rbac/users/${currentUser.id}/roles`);
      return response.data ?? [];
    },
    enabled: Boolean(currentUser?.id),
    initialData: [],
    staleTime: 2 * 60 * 1000,
  });

  const { data: roleHierarchy = [] } = useQuery<RoleHierarchy[], Error>({
    queryKey: ["rbac", "role-hierarchy", userRoles.map((role) => role.id)],
    queryFn: async () => {
      if (!userRoles.length) {
        return [];
      }

      const searchParams = new URLSearchParams();
      for (const role of userRoles) {
        searchParams.append("roleIds", role.id);
      }

      const response = await enhancedApiClient.get<RoleHierarchy[]>(
        `/api/rbac/role-hierarchy?${searchParams.toString()}`
      );

      return response.data ?? [];
    },
    enabled: userRoles.length > 0,
    initialData: [],
    staleTime: 5 * 60 * 1000,
  });

  const { data: evilModeSession = null } = useQuery<EvilModeSession | null, Error>({
    queryKey: ["rbac", "evil-mode-session", currentUser?.id],
    queryFn: async () => {
      if (!currentUser?.id) {
        return null;
      }

      const response = await enhancedApiClient.get<EvilModeSession | null>(
        `/api/rbac/evil-mode/session/${currentUser.id}`
      );
      return response.data ?? null;
    },
    enabled: Boolean(currentUser?.id),
    initialData: null,
    refetchInterval: 30000,
  });

  // Calculate effective permissions
  const effectivePermissions = useMemo(() => {
    if (!userRoles.length) {
      return [];
    }

    const permissions = new Set<Permission>();

    for (const role of userRoles) {
      for (const permission of role.permissions) {
        permissions.add(permission);
      }
    }

    if (currentUser?.directPermissions) {
      for (const permission of currentUser.directPermissions) {
        permissions.add(permission);
      }
    }

    if (rbacConfig.enableRoleHierarchy && roleHierarchy.length) {
      for (const hierarchy of roleHierarchy) {
        for (const permission of hierarchy.effectivePermissions) {
          permissions.add(permission);
        }
      }
    }

    return Array.from(permissions);
  }, [userRoles, currentUser?.directPermissions, rbacConfig.enableRoleHierarchy, roleHierarchy]);

  const checkPermission = useCallback((
    permission: Permission,
    context?: Partial<AccessContext>
  ): PermissionCheckResult => {
    if (!currentUser) {
      return {
        granted: false,
        reason: 'User not authenticated',
        appliedRules: [],
        restrictions: []
      };
    }

    // Check if user has the permission
    const hasDirectPermission = effectivePermissions.includes(permission);
    
    if (!hasDirectPermission) {
      return {
        granted: false,
        reason: `Permission '${permission}' not granted to user`,
        appliedRules: [],
        restrictions: []
      };
    }

    // Check restrictions
    const activeRestrictions: Restriction[] = [
      ...(currentUser.restrictions || []),
      ...userRoles.flatMap(role => role.restrictions || []),
    ].filter(restriction => restriction.active);

    // Apply context-based restrictions
    for (const restriction of activeRestrictions) {
      if (restriction.type === 'time_limit' && context?.timestamp) {
        // Check time-based restrictions
        const timeConfig = restriction.config as { startTime: string; endTime: string };
        const currentTime = context.timestamp.getHours() * 60 + context.timestamp.getMinutes();
        const startTime = parseTime(timeConfig.startTime);
        const endTime = parseTime(timeConfig.endTime);
        
        if (currentTime < startTime || currentTime > endTime) {
          return {
            granted: false,
            reason: `Access restricted outside allowed time window (${timeConfig.startTime}-${timeConfig.endTime})`,
            appliedRules: [],
            restrictions: [restriction]
          };
        }
      }
      
      if (restriction.type === 'ip_restriction' && context?.ipAddress) {
        // Check IP-based restrictions
        const ipConfig = restriction.config as { allowedIPs: string[]; blockedIPs: string[] };
        if (ipConfig.blockedIPs?.includes(context.ipAddress)) {
          return {
            granted: false,
            reason: 'Access denied from this IP address',
            appliedRules: [],
            restrictions: [restriction]
          };
        }
      }
    }

    // Check if Evil Mode is required
    const requiresEvilMode = isEvilModePermission(permission);
    if (requiresEvilMode && !evilModeSession) {
      return {
        granted: false,
        reason: 'Evil Mode required for this operation',
        appliedRules: [],
        restrictions: [],
        requiresElevation: true,
        elevationReason: 'This operation requires Evil Mode activation'
      };
    }

    return {
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: activeRestrictions
    };
  }, [effectivePermissions, currentUser, userRoles, evilModeSession]);

  const hasPermission = useCallback(
    (permission: Permission, context?: Partial<AccessContext>): boolean => {
      return checkPermission(permission, context).granted;
    },
    [checkPermission]
  );

  const hasAnyPermission = useCallback((permissions: Permission[]): boolean => {
    return permissions.some(permission => hasPermission(permission));
  }, [hasPermission]);

  const hasAllPermissions = useCallback((permissions: Permission[]): boolean => {
    return permissions.every(permission => hasPermission(permission));
  }, [hasPermission]);

  // Role management mutations
  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      enhancedApiClient.post(`/api/rbac/users/${userId}/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'user-roles'] });
    }
  });

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      enhancedApiClient.delete(`/api/rbac/users/${userId}/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'user-roles'] });
    }
  });

  // Evil Mode mutations
  const enableEvilModeMutation = useMutation({
    mutationFn: ({ justification, additionalAuth }: { justification: string; additionalAuth?: string }) =>
      enhancedApiClient.post('/api/rbac/evil-mode/enable', {
        justification,
        additionalAuth,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'evil-mode-session'] });
    }
  });

  const disableEvilModeMutation = useMutation({
    mutationFn: () => enhancedApiClient.post('/api/rbac/evil-mode/disable'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'evil-mode-session'] });
    }
  });

  // Helper functions
  const getUserRoles = useCallback(async (userId: string): Promise<Role[]> => {
    const response = await enhancedApiClient.get<Role[]>(`/api/rbac/users/${userId}/roles`);
    return response.data ?? [];
  }, []);

  const assignRole = useCallback(async (userId: string, roleId: string): Promise<void> => {
    await assignRoleMutation.mutateAsync({ userId, roleId });
  }, [assignRoleMutation]);

  const removeRole = useCallback(async (userId: string, roleId: string): Promise<void> => {
    await removeRoleMutation.mutateAsync({ userId, roleId });
  }, [removeRoleMutation]);

  const enableEvilMode = useCallback(
    async (justification: string, additionalAuth?: string): Promise<void> => {
      await enableEvilModeMutation.mutateAsync({ justification, additionalAuth });
    },
    [enableEvilModeMutation],
  );

  const disableEvilMode = useCallback(async (): Promise<void> => {
    await disableEvilModeMutation.mutateAsync();
  }, [disableEvilModeMutation]);

  // Computed values
  const isEvilModeEnabled = !!evilModeSession;
  const canEnableEvilMode = hasPermission("security:evil_mode");
  const isLoading = rolesLoading;
  const isError = rolesError;
  const error = rolesErrorData ?? null;

  const contextValue: RBACContextValue = {
    currentUser,
    userRoles,
    effectivePermissions,
    hasPermission,
    checkPermission,
    hasAnyPermission,
    hasAllPermissions,
    getUserRoles,
    assignRole,
    removeRole,
    isEvilModeEnabled,
    canEnableEvilMode,
    enableEvilMode,
    disableEvilMode,
    evilModeSession,
    rbacConfig,
    evilModeConfig,
    isLoading,
    isError,
    error,
  };

  return (
    <RBACContext.Provider value={contextValue}>
      {children}
    </RBACContext.Provider>
  );
}

export function useRBAC() {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error('useRBAC must be used within an RBACProvider');
  }
  return context;
}

// Helper functions
function getDefaultRBACConfig(): RBACConfig {
  return {
    enableRoleHierarchy: true,
    conflictResolution: "highest_priority",
    sessionTimeout: 30 * 60 * 1000, // 30 minutes
    requireReauthentication: false,
    auditLevel: "detailed",
    cachePermissions: true,
    cacheTTL: 5 * 60 * 1000, // 5 minutes
  };
}

function getDefaultEvilModeConfig(): EvilModeConfig {
  return {
    enabled: true,
    requiredRole: "security:evil_mode",
    confirmationRequired: true,
    additionalAuthRequired: true,
    auditLevel: "comprehensive",
    restrictions: [],
    warningMessage:
      "You are about to enable Evil Mode. This grants elevated privileges that can potentially harm the system. Proceed with extreme caution.",
    timeLimit: 60, // 1 hour
  };
}

function parseTime(timeStr: string): number {
  const [hours, minutes] = timeStr.split(":").map(Number);
  return hours * 60 + minutes;
}

function isEvilModePermission(permission: Permission): boolean {
  const evilModePermissions: Permission[] = [
    "security:evil_mode",
    "system:admin",
    "users:admin",
  ];
  return evilModePermissions.includes(permission);
}

function mapStoreUserToRBACUser(storeUser: NonNullable<AppState["user"]>): User {
  return {
    id: storeUser.id,
    username: storeUser.name || storeUser.email,
    email: storeUser.email,
    roles: storeUser.roles,
    directPermissions: [],
    restrictions: [],
    metadata: {
      createdAt: new Date(),
      lastLogin: undefined,
      isActive: true,
      requiresPasswordChange: false,
    },
  };
}