"use client";

import { createContext } from 'react';
import {
  type AccessContext,
  type EvilModeConfig,
  type EvilModeSession,
  type Permission,
  type PermissionCheckResult,
  type RBACConfig,
  type Role,
  type RBACUser,
} from '@/types/rbac';

export interface RBACContextValue {
  currentUser: RBACUser | null;
  userRoles: Role[];
  effectivePermissions: Permission[];
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
  getUserRoles: (userId: string) => Promise<Role[]>;
  assignRole: (userId: string, roleId: string) => Promise<void>;
  removeRole: (userId: string, roleId: string) => Promise<void>;
  isEvilModeEnabled: boolean;
  canEnableEvilMode: boolean;
  enableEvilMode: (
    justification: string,
    additionalAuth?: string
  ) => Promise<void>;
  disableEvilMode: () => Promise<void>;
  evilModeSession: EvilModeSession | null;
  rbacConfig: RBACConfig;
  evilModeConfig: EvilModeConfig;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

export const RBACContext = createContext<RBACContextValue | null>(null);
