"use client";

import React, {
  useCallback,
  useMemo,
} from "react";
import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  type AccessContext,
  type EvilModeConfig,
  type EvilModeSession,
  type Permission,
  type PermissionCheckResult,
  type RBACConfig,
  type Role,
  type RoleHierarchyItem,
  type Restriction,
  type RBACUser,
} from "@/lib/security/rbac/types";

import { RBACContext, type RBACContextValue } from './rbac-context';

import { enhancedApiClient } from "@/lib/enhanced-api-client";
import { useAppStore } from "@/store/app-store";
import type { User as StoreUser } from "@/store/app-store";

export interface RBACProviderProps {
  children: React.ReactNode;
  config?: Partial<RBACConfig>;
}

/* ----------------------------------------------------------------------------
 * Provider
 * ------------------------------------------------------------------------- */

export function RBACProvider({ children, config }: RBACProviderProps) {
  const queryClient = useQueryClient();
  const appUser = useAppStore((state) => state.user);

  const currentUser = useMemo(
    () => normalizeRBACUser(appUser),
    [appUser]
  );

  /**
   * RBAC base config
   */
  const baseConfig = useMemo<RBACConfig>(
    () => ({
      ...getDefaultRBACConfig(),
      ...(config ?? {}),
    }),
    [config]
  );

  const {
    data: fetchedRBACConfig,
    isLoading: configLoading,
    isError: configError,
    error: configErrorData,
  } = useQuery<RBACConfig, Error>({
    queryKey: ["rbac", "config"],
    queryFn: async () => {
      const response =
        await enhancedApiClient.get<RBACConfig>("/api/rbac/config");
      return response.data
        ? { ...baseConfig, ...response.data }
        : baseConfig;
    },
    initialData: baseConfig,
    staleTime: 5 * 60 * 1000,
  });

  const rbacConfig = useMemo<RBACConfig>(
    () => ({
      ...baseConfig,
      ...(fetchedRBACConfig ?? {}),
    }),
    [baseConfig, fetchedRBACConfig]
  );

  /**
   * Evil Mode configuration
   */
  const {
    data: fetchedEvilModeConfig,
    isLoading: evilModeConfigLoading,
    isError: evilModeConfigError,
    error: evilModeConfigErrorData,
  } = useQuery<EvilModeConfig, Error>({
    queryKey: ["rbac", "evil-mode-config"],
    queryFn: async () => {
      const response =
        await enhancedApiClient.get<EvilModeConfig>(
          "/api/rbac/evil-mode/config"
        );
      return response.data ?? getDefaultEvilModeConfig();
    },
    initialData: getDefaultEvilModeConfig(),
    staleTime: 5 * 60 * 1000,
  });

  const evilModeConfig: EvilModeConfig =
    fetchedEvilModeConfig ?? getDefaultEvilModeConfig();

  /**
   * Roles for current user
   */
  const {
    data: userRoles = [],
    isLoading: rolesLoading,
    isError: rolesError,
    error: rolesErrorData,
  } = useQuery<Role[], Error>({
    queryKey: ["rbac", "user-roles", currentUser?.id],
    queryFn: async () => {
      if (!currentUser?.id) return [];
      const response =
        await enhancedApiClient.get<Role[]>(
          `/api/rbac/users/${currentUser.id}/roles`
        );
      return response.data ?? [];
    },
    enabled: Boolean(currentUser?.id),
    initialData: [],
    staleTime: 2 * 60 * 1000,
  });

  /**
   * Role hierarchy
   */
  const { data: roleHierarchy = [] } = useQuery<RoleHierarchyItem[], Error>({
    queryKey: [
      "rbac",
      "role-hierarchy",
      ...buildRoleHierarchyKey(userRoles),
    ],
    queryFn: async () => {
      if (!userRoles.length) return [];
      const params = new URLSearchParams();
      for (const role of userRoles) {
        params.append("roleIds", role.id);
      }
      const response =
        await enhancedApiClient.get<RoleHierarchyItem[]>(
          `/api/rbac/role-hierarchy?${params.toString()}`
        );
      return response.data ?? [];
    },
    enabled: userRoles.length > 0,
    initialData: [],
    staleTime: 5 * 60 * 1000,
  });

  /**
   * Evil mode session
   */
  const { data: evilModeSession = null } = useQuery<
    EvilModeSession | null,
    Error
  >({
    queryKey: ["rbac", "evil-mode-session", currentUser?.id],
    queryFn: async () => {
      if (!currentUser?.id) return null;
      const response =
        await enhancedApiClient.get<EvilModeSession | null>(
          `/api/rbac/evil-mode/session/${currentUser.id}`
        );
      return response.data ?? null;
    },
    enabled: Boolean(currentUser?.id),
    initialData: null,
    refetchInterval: 30_000,
  });

  /**
   * Effective permissions
   */
  const effectivePermissions: Permission[] = useMemo(() => {
    if (!currentUser && !userRoles.length) return [];

    const permissions = new Set<Permission>();

    for (const role of userRoles) {
      for (const p of role.permissions ?? []) {
        permissions.add(p);
      }
    }

    if (currentUser?.directPermissions) {
      for (const p of currentUser.directPermissions) {
        permissions.add(p);
      }
    }

    if (rbacConfig.enableRoleHierarchy && roleHierarchy.length) {
      for (const hierarchy of roleHierarchy) {
        for (const p of hierarchy.effectivePermissions ?? []) {
          permissions.add(p);
        }
      }
    }

    return Array.from(permissions);
  }, [
    currentUser,
    userRoles,
    rbacConfig.enableRoleHierarchy,
    roleHierarchy,
  ]);

  /**
   * Permission check core
   */
  const checkPermission = useCallback(
    (
      permission: Permission,
      context?: Partial<AccessContext>
    ): PermissionCheckResult => {
      if (!currentUser) {
        return {
          granted: false,
          reason: "User not authenticated",
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
      ].filter((r) => r.active);

      // Time window restriction
      if (context?.timestamp) {
        for (const restriction of activeRestrictions) {
          if (restriction.type === "time_limit") {
            const cfg = restriction
              .config as { startTime: string; endTime: string };
            const nowMinutes =
              context.timestamp.getHours() * 60 +
              context.timestamp.getMinutes();
            const start = parseTime(cfg.startTime);
            const end = parseTime(cfg.endTime);

            if (nowMinutes < start || nowMinutes > end) {
              return {
                granted: false,
                reason: `Access restricted outside allowed time window (${cfg.startTime}-${cfg.endTime})`,
                appliedRules: [],
                restrictions: [restriction],
              };
            }
          }
        }
      }

      // IP restriction
      if (context?.ipAddress) {
        for (const restriction of activeRestrictions) {
          if (restriction.type === "ip_restriction") {
            const ipCfg = normalizeIPRestrictionConfig(
              restriction.config || {}
            );
            if (
              ipCfg.blockedIPs.includes(context.ipAddress) ||
              (ipCfg.allowedIPs.length > 0 &&
                !ipCfg.allowedIPs.includes(context.ipAddress))
            ) {
              return {
                granted: false,
                reason: "Access denied from this IP address",
                appliedRules: [],
                restrictions: [restriction],
              };
            }
          }
        }
      }

      // Evil Mode gating
      if (isEvilModePermission(permission)) {
        if (!evilModeConfig.enabled) {
          return {
            granted: false,
            reason:
              "Evil Mode operations are disabled by configuration",
            appliedRules: [],
            restrictions: activeRestrictions,
          };
        }

        if (!evilModeSession) {
          return {
            granted: false,
            reason: "Evil Mode required for this operation",
            appliedRules: [],
            restrictions: activeRestrictions,
            requiresElevation: true,
            elevationReason:
              "This operation requires an active Evil Mode session",
          };
        }
      }

      return {
        granted: true,
        reason: "Permission granted",
        appliedRules: [],
        restrictions: activeRestrictions,
      };
    },
    [
      currentUser,
      effectivePermissions,
      userRoles,
      evilModeSession,
      evilModeConfig.enabled,
    ]
  );

  const hasPermission = useCallback(
    (permission: Permission, context?: Partial<AccessContext>): boolean => {
      const result = checkPermission(permission, context);
      return result.granted ?? false;
    },
    [checkPermission]
  );

  const hasAnyPermission = useCallback(
    (permissions: Permission[]): boolean =>
      permissions.some((p) => hasPermission(p)),
    [hasPermission]
  );

  const hasAllPermissions = useCallback(
    (permissions: Permission[]): boolean =>
      permissions.every((p) => hasPermission(p)),
    [hasPermission]
  );

  /* ----------------------------------------------------------------------------
   * Mutations: roles & evil mode
   * ------------------------------------------------------------------------- */

  const assignRoleMutation = useMutation({
    mutationFn: async ({
      userId,
      roleId,
    }: {
      userId: string;
      roleId: string;
    }) => {
      await enhancedApiClient.post(
        `/api/rbac/users/${userId}/roles/${roleId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rbac", "user-roles"],
      });
    },
  });

  const removeRoleMutation = useMutation({
    mutationFn: async ({
      userId,
      roleId,
    }: {
      userId: string;
      roleId: string;
    }) => {
      await enhancedApiClient.delete(
        `/api/rbac/users/${userId}/roles/${roleId}`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rbac", "user-roles"],
      });
    },
  });

  const enableEvilModeMutation = useMutation({
    mutationFn: async (payload: {
      justification: string;
      additionalAuth?: string;
    }) => {
      await enhancedApiClient.post(
        "/api/rbac/evil-mode/enable",
        payload
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rbac", "evil-mode-session"],
      });
    },
  });

  const disableEvilModeMutation = useMutation({
    mutationFn: async () => {
      await enhancedApiClient.post(
        "/api/rbac/evil-mode/disable"
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["rbac", "evil-mode-session"],
      });
    },
  });

  const getUserRoles = useCallback(
    async (userId: string): Promise<Role[]> => {
      const response =
        await enhancedApiClient.get<Role[]>(
          `/api/rbac/users/${userId}/roles`
        );
      return response.data ?? [];
    },
    []
  );

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
    async (
      justification: string,
      additionalAuth?: string
    ): Promise<void> => {
      await enableEvilModeMutation.mutateAsync({
        justification,
        additionalAuth,
      });
    },
    [enableEvilModeMutation]
  );

  const disableEvilMode = useCallback(
    async (): Promise<void> => {
      await disableEvilModeMutation.mutateAsync();
    },
    [disableEvilModeMutation]
  );

  /* ----------------------------------------------------------------------------
   * Derived flags
   * ------------------------------------------------------------------------- */

  const isEvilModeEnabled = Boolean(evilModeSession);
  const canEnableEvilMode = hasPermission("security:evil_mode");

  const isLoading =
    configLoading ||
    evilModeConfigLoading ||
    rolesLoading ||
    enableEvilModeMutation.isPending ||
    disableEvilModeMutation.isPending ||
    assignRoleMutation.isPending ||
    removeRoleMutation.isPending;

  const isError =
    configError || evilModeConfigError || rolesError || false;

  const error: Error | null =
    rolesErrorData ??
    configErrorData ??
    evilModeConfigErrorData ??
    null;

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

/* ----------------------------------------------------------------------------
 * Hook
 * ------------------------------------------------------------------------- */

/* ----------------------------------------------------------------------------
 * Defaults & Helpers
 * ------------------------------------------------------------------------- */

function getDefaultRBACConfig(): RBACConfig {
  return {
    enableCache: true,
    cacheTTL: 5 * 60 * 1000,
    enableDebugLogging: false,
    enableStrictMode: false,
    enableDynamicPermissions: true,
    defaultRole: "user",
    guestRole: "guest",
    enableRoleHierarchy: true,
    conflictResolution: "highest_priority",
    sessionTimeout: 30 * 60 * 1000,
    requireReauthentication: false,
    auditLevel: "detailed",
    cachePermissions: true,
  };
}

function getDefaultEvilModeConfig(): EvilModeConfig {
  return {
    enabled: true,
    justificationRequired: true,
    timeout: 60,
    timeLimit: 60,
    maxActions: 100,
    auditLogging: true,
    notificationEnabled: true,
    allowedRoles: ["admin"],
    requiredRole: "security:evil_mode",
    confirmationRequired: true,
    additionalAuthRequired: true,
    auditLevel: "comprehensive",
    restrictions: [],
    warningMessage:
      "You are about to enable Evil Mode. This grants elevated privileges that can potentially harm the system. Proceed with extreme caution.",
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

function buildRoleHierarchyKey(userRoles: Role[]): string[] {
  if (!userRoles.length) return [];
  return [...new Set(userRoles.map((r) => r.id))].sort();
}

type RBACMetadataInput = Partial<{
  createdAt: Date | string | number;
  lastLogin: Date | string | number;
  isActive: boolean;
  requiresPasswordChange: boolean;
}>;

function parseDate(value: unknown): Date | undefined {
  if (value instanceof Date) {
    return value;
  }
  if (typeof value === "string" || typeof value === "number") {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? undefined : parsed;
  }
  return undefined;
}

function normalizeRBACUser(
  user: StoreUser | RBACUser | null | undefined
): RBACUser | null {
  if (!user) return null;

  const candidate = user as RBACUser & StoreUser;
  const metadataInput: RBACMetadataInput = candidate.metadata ?? {};

  const normalizedMetadata = {
    createdAt: parseDate(metadataInput.createdAt) ?? new Date(),
    lastLogin: parseDate(metadataInput.lastLogin),
    isActive:
      typeof metadataInput.isActive === "boolean"
        ? metadataInput.isActive
        : true,
    requiresPasswordChange:
      metadataInput.requiresPasswordChange ?? false,
  };

  return {
    id: candidate.id,
    username:
      candidate.username ??
      candidate.name ??
      candidate.email ??
      candidate.id,
    email: candidate.email,
    roles: Array.isArray(candidate.roles) ? candidate.roles : [],
    is_active: candidate.is_active ?? true,
    directPermissions: candidate.directPermissions ?? [],
    restrictions: candidate.restrictions ?? [],
    metadata: normalizedMetadata,
  };
}

function normalizeIPRestrictionConfig(
  config: Record<string, unknown>
): { allowedIPs: string[]; blockedIPs: string[] } {
  const resolveIpList = (value: unknown): string[] =>
    Array.isArray(value)
      ? value.filter((entry): entry is string => typeof entry === "string")
      : [];

  const rawAllowed = config["allowedIPs"];
  const rawBlocked = config["blockedIPs"];

  return {
    allowedIPs: resolveIpList(rawAllowed),
    blockedIPs: resolveIpList(rawBlocked),
  };
}
