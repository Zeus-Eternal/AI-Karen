"use client";

import React, { createContext, useContext, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  AccessContext,
  EvilModeConfig,
  EvilModeSession,
  Permission,
  PermissionCheckResult,
  RBACConfig,
  Role,
  RoleHierarchy,
  Restriction,
  RBACUser,
} from '@/types/rbac';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { useAppStore } from '@/store/app-store';
import type { User as StoreUser } from '@/store/app-store';

export interface RBACContextValue {
  // Current user and permissions
  currentUser: RBACUser | null;
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
  const { user: appUser } = useAppStore();

  const currentUser = useMemo(() => normalizeRBACUser(appUser), [appUser]);

  const {
    data: fetchedRBACConfig,
    isLoading: configLoading,
    isError: configError,
    error: configErrorData,
  } = useQuery<RBACConfig, Error>({
    queryKey: ['rbac', 'config'],
    queryFn: async () => {
      const response = await enhancedApiClient.get<RBACConfig>('/api/rbac/config');
      return response.data ?? getDefaultRBACConfig();
    },
    staleTime: 5 * 60 * 1000,
  });

  const rbacConfig = useMemo(() => {
    const baseConfig = fetchedRBACConfig ?? getDefaultRBACConfig();
    return {
      ...baseConfig,
      ...(config ?? {}),
    };
  }, [config, fetchedRBACConfig]);

  const {
    data: fetchedEvilModeConfig,
    isLoading: evilModeConfigLoading,
    isError: evilModeConfigError,
    error: evilModeConfigErrorData,
  } = useQuery<EvilModeConfig, Error>({
    queryKey: ['rbac', 'evil-mode-config'],
    queryFn: async () => {
      const response = await enhancedApiClient.get<EvilModeConfig>('/api/rbac/evil-mode/config');
      return response.data ?? getDefaultEvilModeConfig();
    },
    staleTime: 5 * 60 * 1000,
  });

  const evilModeConfig = fetchedEvilModeConfig ?? getDefaultEvilModeConfig();

  const {
    data: userRoles = [],
    isLoading: rolesLoading,
    isError: rolesError,
    error: rolesErrorData,
  } = useQuery<Role[], Error>({
    queryKey: ['rbac', 'user-roles', currentUser?.id],
    queryFn: async () => {
      if (!currentUser) {
        return [];
      }

      const response = await enhancedApiClient.get<Role[]>(`/api/rbac/users/${currentUser.id}/roles`);
      return response.data ?? [];
    },
    enabled: Boolean(currentUser?.id),
    staleTime: 2 * 60 * 1000,
  });

  const { data: roleHierarchy = [] } = useQuery<RoleHierarchy[], Error>({
    queryKey: ['rbac', 'role-hierarchy', buildRoleHierarchyKey(userRoles)],
    queryFn: async () => {
      const params = new URLSearchParams();
      userRoles.forEach((role) => params.append('roleIds', role.id));
      const queryString = params.toString();
      const endpoint = queryString
        ? `/api/rbac/role-hierarchy?${queryString}`
        : '/api/rbac/role-hierarchy';
      const response = await enhancedApiClient.get<RoleHierarchy[]>(endpoint);
      return response.data ?? [];
    },
    enabled: userRoles.length > 0,
    staleTime: 5 * 60 * 1000,
  });

  const { data: evilModeSession = null } = useQuery<EvilModeSession | null, Error>({
    queryKey: ['rbac', 'evil-mode-session', currentUser?.id],
    queryFn: async () => {
      if (!currentUser) {
        return null;
      }

      const response = await enhancedApiClient.get<EvilModeSession | null>(
        `/api/rbac/evil-mode/session/${currentUser.id}`
      );
      return response.data ?? null;
    },
    enabled: Boolean(currentUser?.id),
    refetchInterval: 30000,
  });

  const effectivePermissions = useMemo(() => {
    if (!userRoles.length && !currentUser?.directPermissions?.length) {
      return [];
    }

    const permissions = new Set<Permission>();

    userRoles.forEach((role) => {
      role.permissions.forEach((permission) => permissions.add(permission));
    });

    currentUser?.directPermissions?.forEach((permission) => permissions.add(permission));

    if (rbacConfig.enableRoleHierarchy && roleHierarchy.length) {
      roleHierarchy.forEach((hierarchy) => {
        hierarchy.effectivePermissions.forEach((permission) => permissions.add(permission));
      });
    }

    return Array.from(permissions);
  }, [currentUser?.directPermissions, rbacConfig.enableRoleHierarchy, roleHierarchy, userRoles]);

  const checkPermission = useCallback(
    (permission: Permission, context?: Partial<AccessContext>): PermissionCheckResult => {
      if (!currentUser) {
        return {
          granted: false,
          reason: 'User not authenticated',
          appliedRules: [],
          restrictions: [],
        };
      }

      if (!effectivePermissions.includes(permission)) {
        return {
          granted: false,
          reason: `Permission '${permission}' not granted to user`,
          appliedRules: [],
          restrictions: [],
        };
      }

      const activeRestrictions: Restriction[] = [
        ...(currentUser.restrictions ?? []),
        ...userRoles.flatMap((role) => role.restrictions ?? []),
      ].filter((restriction) => restriction.active);

      for (const restriction of activeRestrictions) {
        if (restriction.type === 'time_limit' && context?.timestamp) {
          const timeConfig = restriction.config as { startTime: string; endTime: string };
          const currentTime = context.timestamp.getHours() * 60 + context.timestamp.getMinutes();
          const startTime = parseTime(timeConfig.startTime);
          const endTime = parseTime(timeConfig.endTime);

          if (currentTime < startTime || currentTime > endTime) {
            return {
              granted: false,
              reason: `Access restricted outside allowed time window (${timeConfig.startTime}-${timeConfig.endTime})`,
              appliedRules: [],
              restrictions: [restriction],
            };
          }
        }

        if (restriction.type === 'ip_restriction' && context?.ipAddress) {
          const ipConfig = normalizeIPRestrictionConfig(restriction.config);
          if (ipConfig.blockedIPs.includes(context.ipAddress)) {
            return {
              granted: false,
              reason: 'Access denied from this IP address',
              appliedRules: [],
              restrictions: [restriction],
            };
          }
        }
      }

      const requiresEvilMode = isEvilModePermission(permission);
      if (requiresEvilMode && !evilModeSession) {
        return {
          granted: false,
          reason: 'Evil Mode required for this operation',
          appliedRules: [],
          restrictions: activeRestrictions,
          requiresElevation: true,
          elevationReason: 'This operation requires Evil Mode activation',
        };
      }

      return {
        granted: true,
        reason: 'Permission granted',
        appliedRules: [],
        restrictions: activeRestrictions,
      };
    },
    [currentUser, effectivePermissions, evilModeSession, userRoles]
  );

  const hasPermission = useCallback(
    (permission: Permission, context?: Partial<AccessContext>) => checkPermission(permission, context).granted,
    [checkPermission]
  );

  const hasAnyPermission = useCallback(
    (permissions: Permission[]): boolean => permissions.some((permission) => hasPermission(permission)),
    [hasPermission]
  );

  const hasAllPermissions = useCallback(
    (permissions: Permission[]): boolean => permissions.every((permission) => hasPermission(permission)),
    [hasPermission]
  );

  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      enhancedApiClient.post(`/api/rbac/users/${userId}/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'user-roles'] });
    },
  });

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      enhancedApiClient.delete(`/api/rbac/users/${userId}/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'user-roles'] });
    },
  });

  const enableEvilModeMutation = useMutation({
    mutationFn: ({ justification, additionalAuth }: { justification: string; additionalAuth?: string }) =>
      enhancedApiClient.post('/api/rbac/evil-mode/enable', {
        justification,
        additionalAuth,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'evil-mode-session'] });
    },
  });

  const disableEvilModeMutation = useMutation({
    mutationFn: () => enhancedApiClient.post('/api/rbac/evil-mode/disable'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'evil-mode-session'] });
    },
  });

  const getUserRoles = useCallback(async (userId: string): Promise<Role[]> => {
    const response = await enhancedApiClient.get<Role[]>(`/api/rbac/users/${userId}/roles`);
    return response.data ?? [];
  }, []);

  const assignRole = useCallback(
    async (userId: string, roleId: string): Promise<void> => {
      await assignRoleMutation.mutateAsync({ userId, roleId });
    },
    [assignRoleMutation]
  );

  const removeRole = useCallback(
    async (userId: string, roleId: string): Promise<void> => {
      await removeRoleMutation.mutateAsync({ userId, roleId });
    },
    [removeRoleMutation]
  );

  const enableEvilMode = useCallback(
    async (justification: string, additionalAuth?: string): Promise<void> => {
      await enableEvilModeMutation.mutateAsync({ justification, additionalAuth });
    },
    [enableEvilModeMutation]
  );

  const disableEvilMode = useCallback(async (): Promise<void> => {
    await disableEvilModeMutation.mutateAsync();
  }, [disableEvilModeMutation]);

  const isEvilModeEnabled = Boolean(evilModeSession);
  const canEnableEvilMode = hasPermission('security:evil_mode');

  const isLoading = configLoading || rolesLoading || evilModeConfigLoading;
  const isError = configError || rolesError || evilModeConfigError;
  const error = rolesErrorData ?? configErrorData ?? evilModeConfigErrorData ?? null;

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

  return <RBACContext.Provider value={contextValue}>{children}</RBACContext.Provider>;
}

export function useRBAC() {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error('useRBAC must be used within an RBACProvider');
  }
  return context;
}

function getDefaultRBACConfig(): RBACConfig {
  return {
    enableRoleHierarchy: true,
    conflictResolution: 'highest_priority',
    sessionTimeout: 30 * 60 * 1000,
    requireReauthentication: false,
    auditLevel: 'detailed',
    cachePermissions: true,
    cacheTTL: 5 * 60 * 1000,
  };
}

function getDefaultEvilModeConfig(): EvilModeConfig {
  return {
    enabled: true,
    requiredRole: 'security:evil_mode',
    confirmationRequired: true,
    additionalAuthRequired: true,
    auditLevel: 'comprehensive',
    restrictions: [],
    warningMessage:
      'You are about to enable Evil Mode. This grants elevated privileges that can potentially harm the system. Proceed with extreme caution.',
    timeLimit: 60,
  };
}

function parseTime(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

function isEvilModePermission(permission: Permission): boolean {
  const evilModePermissions: Permission[] = ['security:evil_mode', 'system:admin', 'users:admin'];
  return evilModePermissions.includes(permission);
}

function buildRoleHierarchyKey(userRoles: Role[]): string[] {
  if (!userRoles.length) {
    return [];
  }

  return [...new Set(userRoles.map((role) => role.id))].sort();
}

function normalizeRBACUser(user: StoreUser | RBACUser | null | undefined): RBACUser | null {
  if (!user) {
    return null;
  }

  const candidate = user as RBACUser & StoreUser;

  const metadata = candidate.metadata ?? {
    createdAt: new Date(),
    isActive: true,
    requiresPasswordChange: false,
  };

  return {
    id: candidate.id,
    username: candidate.username ?? candidate.name ?? candidate.email ?? candidate.id,
    email: candidate.email,
    roles: Array.isArray(candidate.roles) ? candidate.roles : [],
    directPermissions: candidate.directPermissions ?? [],
    restrictions: candidate.restrictions ?? [],
    metadata: {
      createdAt: metadata.createdAt instanceof Date ? metadata.createdAt : new Date(metadata.createdAt ?? Date.now()),
      lastLogin:
        metadata.lastLogin instanceof Date
          ? metadata.lastLogin
          : metadata.lastLogin
          ? new Date(metadata.lastLogin)
          : undefined,
      isActive: metadata.isActive ?? true,
      requiresPasswordChange: metadata.requiresPasswordChange ?? false,
    },
  };
}

function normalizeIPRestrictionConfig(
  config: Record<string, string | number | boolean>
): { allowedIPs: string[]; blockedIPs: string[] } {
  const allowed = Array.isArray((config as Record<string, unknown>).allowedIPs)
    ? ((config as Record<string, unknown>).allowedIPs as unknown[]).filter((value): value is string => typeof value === 'string')
    : [];
  const blocked = Array.isArray((config as Record<string, unknown>).blockedIPs)
    ? ((config as Record<string, unknown>).blockedIPs as unknown[]).filter((value): value is string => typeof value === 'string')
    : [];

  return {
    allowedIPs: allowed,
    blockedIPs: blocked,
  };
}
