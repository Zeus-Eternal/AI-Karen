"use client";

import React, {
  createContext,
  useContext,
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
  type RoleHierarchy,
  type Restriction,
  type RBACUser,
} from "@/types/rbac";

import { enhancedApiClient } from "@/lib/enhanced-api-client";
import { useAppStore } from "@/store/app-store";
import type { User as StoreUser } from "@/store/app-store";

/* ----------------------------------------------------------------------------
 * Context Types
 * ------------------------------------------------------------------------- */

export interface RBACContextValue {
  // Current user and permissions
  currentUser: RBACUser | null;
  userRoles: Role[];
  effectivePermissions: Permission[];

  // Permission checking
  hasPermission: (
    permission: Permission,
    context?: Partial<AccessContext>
  ) => boolean;
  checkPermission: (
    permission: Permission,
    context?: Partial<AccessContext>
  ) => PermissionCheckResult;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;

  // Role management
  getUserRoles: (userId: string) => Promise<Role[]>;
  assignRole: (userId: string, roleId: string) => Promise<void>;
  removeRole: (userId: string, roleId: string) => Promise<void>;

  // Evil Mode
  isEvilModeEnabled: boolean;
  canEnableEvilMode: boolean;
  enableEvilMode: (
    justification: string,
    additionalAuth?: string
  ) => Promise<void>;
  disableEvilMode: () => Promise<void>;
  evilModeSession: EvilModeSession | null;

  // Configuration
  rbacConfig: RBACConfig;
  evilModeConfig: EvilModeConfig;

  // Loading / error state
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

const RBACContext = createContext<RBACContextValue | null>(null);

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
  const { data: roleHierarchy = [] } = useQuery<RoleHierarchy[], Error>({
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
        await enhancedApiClient.get<RoleHierarchy[]>(
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
              restriction.config
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
    (permission: Permission, context?: Partial<AccessContext>): boolean =>
      checkPermission(permission, context).granted,
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

export function useRBAC(): RBACContextValue {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error("useRBAC must be used within an RBACProvider");
  }
  return context;
}

/* ----------------------------------------------------------------------------
 * Defaults & Helpers
 * ------------------------------------------------------------------------- */

function getDefaultRBACConfig(): RBACConfig {
  return {
    enableRoleHierarchy: true,
    conflictResolution: "highest_priority",
    sessionTimeout: 30 * 60 * 1000,
    requireReauthentication: false,
    auditLevel: "detailed",
    cachePermissions: true,
    cacheTTL: 5 * 60 * 1000,
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
    timeLimit: 60,
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

function normalizeRBACUser(
  user: StoreUser | RBACUser | null | undefined
): RBACUser | null {
  if (!user) return null;

  const candidate = user as RBACUser & StoreUser;
  const metadata = candidate.metadata ?? {
    createdAt: new Date(),
    isActive: true,
    requiresPasswordChange: false,
  };

  return {
    id: candidate.id,
    username:
      candidate.username ??
      candidate.name ??
      candidate.email ??
      candidate.id,
    email: candidate.email,
    roles: Array.isArray(candidate.roles)
      ? candidate.roles
      : [],
    directPermissions: candidate.directPermissions ?? [],
    restrictions: candidate.restrictions ?? [],
    metadata: {
      createdAt:
        metadata.createdAt instanceof Date
          ? metadata.createdAt
          : new Date(
              (metadata as any).createdAt ?? Date.now()
            ),
      lastLogin:
        metadata.lastLogin instanceof Date
          ? metadata.lastLogin
          : metadata.lastLogin
          ? new Date(metadata.lastLogin as any)
          : undefined,
      isActive:
        typeof metadata.isActive === "boolean"
          ? metadata.isActive
          : true,
      requiresPasswordChange:
        metadata.requiresPasswordChange ?? false,
    },
  };
}

function normalizeIPRestrictionConfig(
  config: Record<string, unknown>
): { allowedIPs: string[]; blockedIPs: string[] } {
  const rawAllowed = (config as any).allowedIPs;
  const rawBlocked = (config as any).blockedIPs;

  const allowedIPs = Array.isArray(rawAllowed)
    ? rawAllowed.filter((v): v is string => typeof v === "string")
    : [];

  const blockedIPs = Array.isArray(rawBlocked)
    ? rawBlocked.filter((v): v is string => typeof v === "string")
    : [];

  return { allowedIPs, blockedIPs };
}
