/**
 * Centralized Hook Mocking Utilities (Vitest)
 * ------------------------------------------
 * Consistent, reusable mocking strategies for authentication/role hooks.
 *
 * Design goals:
 * - Do NOT call vi.mock() at import-time. Tests own mocking.
 * - Provide factories + scenarios to keep tests terse and isolated.
 * - Mirror AuthContext semantics so components behave realistically.
 */

// Vitest globals are configured via tsconfig types; keep usage implicit.
import type { AuthContextType, User, LoginCredentials } from '@/contexts/AuthContext';
import type { UseRoleReturn } from '@/hooks/useRole';
import { mockSuperAdminUser, mockAdminUser, mockRegularUser, createMockAuthContext } from './test-providers';

type AuthRole = Parameters<AuthContextType['hasRole']>[0];

// ---------------------------------------------------------------------------
// Internal registry (for optional debugging)
// ---------------------------------------------------------------------------
const activeMocks = new Set<string>();

// ---------------------------------------------------------------------------
// Lightweight global mock bootstrap
// ---------------------------------------------------------------------------

const createDefaultAuthAndRole = () => {
  const auth = createMockAuthContext(null, false);
  const role = createUseRoleReturnFromAuth(auth);
  return { auth, role };
};

export const setupGlobalMocks = () => {
  const restoreFns: Array<() => void> = [];
  let authModule: { useAuth: () => AuthContextType } | null = null;

  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    authModule = require('@/contexts/AuthContext');
    if (authModule && !vi.isMockFunction(authModule.useAuth)) {
      const authSpy = vi
        .spyOn(authModule, 'useAuth')
        .mockImplementation(() => createMockAuthContext(null, false));
      restoreFns.push(() => authSpy.mockRestore());
    }
  } catch {
    authModule = null;
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const roleModule = require('@/hooks/useRole') as { useRole: () => UseRoleReturn };
    if (!vi.isMockFunction(roleModule.useRole)) {
      const roleSpy = vi.spyOn(roleModule, 'useRole').mockImplementation(() => {
        const { auth } = createDefaultAuthAndRole();
        const context = authModule ? authModule.useAuth() : auth;
        return createUseRoleReturnFromAuth(context);
      });
      restoreFns.push(() => roleSpy.mockRestore());
    }
  } catch {
    // Hooks may not exist in certain testing contexts; ignore.
  }

  return () => {
    restoreFns.splice(0).forEach((restore) => {
      try {
        restore();
      } catch {
        // ignore restoration failures – spies may have been manually restored
      }
    });
  };
};

// ---------------------------------------------------------------------------
// Factories that your tests can pass directly to vi.mock(..., factory)
// ---------------------------------------------------------------------------

/**
 * Build a module factory compatible with `vi.mock('@/contexts/AuthContext', factory)`
 */
export const makeUseAuthMockModule = (ctx: AuthContextType) => ({
  __esModule: true as const,
  useAuth: () => ctx,
});

/**
 * Build a module factory compatible with `vi.mock('@/hooks/useRole', factory)`
 */
export const makeUseRoleMockModule = (ret: UseRoleReturn) => ({
  __esModule: true as const,
  useRole: () => ret,
});

// ---------------------------------------------------------------------------
// Lightweight registrars (no vi.mock side-effects here)
// ---------------------------------------------------------------------------
export const setupUseAuthMock = () => {
  const id = 'useAuth';
  activeMocks.add(id);
  return id;
};

export const setupUseRoleMock = () => {
  const id = 'useRole';
  activeMocks.add(id);
  return id;
};

// ---------------------------------------------------------------------------
// Derivations
// ---------------------------------------------------------------------------
export const createUseRoleReturnFromAuth = (authContext: AuthContextType): UseRoleReturn => {
  const role = authContext.user?.role ?? null;
  return {
    role,
    hasRole: authContext.hasRole,
    hasPermission: authContext.hasPermission,
    isAdmin: authContext.isAdmin(),
    isSuperAdmin: authContext.isSuperAdmin(),
    isUser: authContext.hasRole('user'),
    canManageUsers: authContext.hasPermission('user_management'),
    canManageAdmins: authContext.hasPermission('admin_management'),
    canManageSystem: authContext.hasPermission('system_config'),
    canViewAuditLogs: authContext.hasPermission('audit_logs'),
  };
};

// ---------------------------------------------------------------------------
// Scenarios
// ---------------------------------------------------------------------------
export const setupAuthAndRoleMocks = (
  authContext?: AuthContextType,
  roleReturn?: UseRoleReturn,
) => {
  const resolvedAuth = authContext ?? createMockAuthContext();
  const resolvedRole = roleReturn ?? createUseRoleReturnFromAuth(resolvedAuth);
  const authMockId = setupUseAuthMock();
  const roleMockId = setupUseRoleMock();
  return { authMockId, roleMockId, authContext: resolvedAuth, roleReturn: resolvedRole };
};

export const mockScenarios = {
  superAdmin: () => {
    const auth = createMockAuthContext(mockSuperAdminUser, true);
    const role = createUseRoleReturnFromAuth(auth);
    return setupAuthAndRoleMocks(auth, role);
  },
  admin: () => {
    const auth = createMockAuthContext(mockAdminUser, true);
    const role = createUseRoleReturnFromAuth(auth);
    return setupAuthAndRoleMocks(auth, role);
  },
  user: () => {
    const auth = createMockAuthContext(mockRegularUser, true);
    const role = createUseRoleReturnFromAuth(auth);
    return setupAuthAndRoleMocks(auth, role);
  },
  unauthenticated: () => {
    const auth = createMockAuthContext(null, false);
    const role = createUseRoleReturnFromAuth(auth);
    return setupAuthAndRoleMocks(auth, role);
  },
  authError: () => {
    const auth = createMockAuthContext(null, false, {
      login: vi.fn().mockRejectedValue(new Error('Authentication failed')),
      checkAuth: vi.fn().mockRejectedValue(new Error('Authentication failed')),
    });
    const role = createUseRoleReturnFromAuth(auth);
    return setupAuthAndRoleMocks(auth, role);
  },
  sessionExpired: () => {
    const auth = createMockAuthContext(null, false, {
      checkAuth: vi.fn().mockResolvedValue(false),
      logout: vi.fn(),
    });
    const role = createUseRoleReturnFromAuth(auth);
    return setupAuthAndRoleMocks(auth, role);
  },
};

// ---------------------------------------------------------------------------
// Direct creators (do not touch vi.mock)
// ---------------------------------------------------------------------------
export const createMockUseAuth = (
  user: User | null = null,
  isAuthenticated = false,
  overrides: Partial<AuthContextType> = {},
): AuthContextType => createMockAuthContext(user, isAuthenticated, overrides);

export const createMockUseRole = (
  user: User | null = null,
  overrides: Partial<UseRoleReturn> = {},
): UseRoleReturn => {
  const role = user?.role ?? null;
  const base: UseRoleReturn = {
    role,
    hasRole: vi.fn((requiredRole: AuthRole) => {
      if (!user) return false;
      if (user.role) return user.role === requiredRole;
      return user.roles.includes(requiredRole);
    }),
    hasPermission: vi.fn((permission: string) => !!user?.permissions?.includes(permission)),
    isAdmin: !!(user && (user.role === 'admin' || user.role === 'super_admin')),
    isSuperAdmin: !!(user && user.role === 'super_admin'),
    isUser: !!(user && user.role === 'user'),
    canManageUsers: !!user?.permissions?.includes('user_management'),
    canManageAdmins: !!user?.permissions?.includes('admin_management'),
    canManageSystem: !!user?.permissions?.includes('system_config'),
    canViewAuditLogs: !!user?.permissions?.includes('audit_logs'),
  };
  return { ...base, ...overrides };
};

// ---------------------------------------------------------------------------
// Realistic AuthContext (mirrors real behavior for most tests)
// ---------------------------------------------------------------------------
export const createRealisticMockAuth = (user: User | null, isAuthenticated: boolean): AuthContextType => {
  const hasRole = vi.fn((role: AuthRole): boolean => {
    if (!user) return false;
    if (user.role) return user.role === role;
    return !!user.roles?.includes(role);
  });

  const hasPermission = vi.fn((permission: string): boolean => {
    if (!user) return false;
    if (user.permissions) return user.permissions.includes(permission);
    const fallbackRole = (user.role || user.roles?.[0] || 'user') as AuthRole;
    const rolePerms = getRolePermissions(fallbackRole);
    return rolePerms.includes(permission);
  });

  const isAdmin = vi.fn(() => hasRole('admin') || hasRole('super_admin'));
  const isSuperAdmin = vi.fn(() => hasRole('super_admin'));

  return {
    user,
    isAuthenticated,
    authState: {
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: new Date(),
    },
    login: vi.fn(async (_credentials: LoginCredentials) => {}),
    logout: vi.fn(() => {}),
    checkAuth: vi.fn(async () => isAuthenticated),
    refreshSession: vi.fn(async () => isAuthenticated),
    clearError: vi.fn(() => {}),
    hasRole,
    hasPermission,
    isAdmin,
    isSuperAdmin,
  };
};

const getRolePermissions = (role: AuthRole): string[] => {
  switch (role) {
    case 'super_admin':
      return [
        'user_management',
        'admin_management',
        'system_config',
        'audit_logs',
        'security_settings',
        'user_create',
        'user_edit',
        'user_delete',
        'admin_create',
        'admin_edit',
        'admin_delete',
      ];
    case 'admin':
      return ['user_management', 'user_create', 'user_edit', 'user_delete'];
    case 'user':
    default:
      return [];
  }
};

// ---------------------------------------------------------------------------
// Isolation & cleanup
// ---------------------------------------------------------------------------
export const resetHookMocks = () => {
  vi.clearAllMocks();
  vi.resetAllMocks();
};

export const cleanupHookMocks = () => {
  activeMocks.clear();
  resetHookMocks();
};

// ---------------------------------------------------------------------------
// Consistent batch setup / validation / debug
// ---------------------------------------------------------------------------
export const setupConsistentMocks = (scenario: keyof typeof mockScenarios) => mockScenarios[scenario]();

export const validateMockSetup = (authContext: AuthContextType, roleReturn: UseRoleReturn): boolean => {
  const authRole = authContext.user?.role ?? null;
  const roleRole = roleReturn.role ?? null;
  if (authRole && roleRole) return authRole === roleRole;
  return !authRole && !roleRole;
};

export const debugMockState = (authContext: AuthContextType, roleReturn: UseRoleReturn) => {
  // eslint-disable-next-line no-console
  console.debug('[hook-mocking-utils] auth.user', authContext.user);
  // eslint-disable-next-line no-console
  console.debug('[hook-mocking-utils] role.role', roleReturn.role);
};

// ---------------------------------------------------------------------------
// Convenience wrappers
// ---------------------------------------------------------------------------
export const mockAuthForTest = (scenario: keyof typeof mockScenarios) => {
  const { authContext, roleReturn } = mockScenarios[scenario]();
  return { authContext, roleReturn };
};

export const mockAuthWithUser = (user: User | null, isAuthenticated = !!user) => {
  const auth = createRealisticMockAuth(user, isAuthenticated);
  const role = createUseRoleReturnFromAuth(auth);
  return setupAuthAndRoleMocks(auth, role);
};

export const createTestMocks = (options: {
  user?: User | null;
  isAuthenticated?: boolean;
  authOverrides?: Partial<AuthContextType>;
  roleOverrides?: Partial<UseRoleReturn>;
}) => {
  const { user = null, isAuthenticated = false, authOverrides = {}, roleOverrides = {} } = options;
  const baseAuth = createRealisticMockAuth(user, isAuthenticated);
  const auth = { ...baseAuth, ...authOverrides } as AuthContextType;
  const baseRole = createUseRoleReturnFromAuth(auth);
  const role = { ...baseRole, ...roleOverrides } as UseRoleReturn;
  return setupAuthAndRoleMocks(auth, role);
};

// ---------------------------------------------------------------------------
// Global reset helper (safe if modules are mocked)
// ---------------------------------------------------------------------------
export const resetToDefaultMocks = () => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { useAuth } = require('@/contexts/AuthContext');
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { useRole } = require('@/hooks/useRole');

    if (vi.isMockFunction(useAuth)) {
      (useAuth as any).mockReturnValue(
        createMockAuthContext(null, false),
      );
    }
    if (vi.isMockFunction(useRole)) {
      (useRole as any).mockReturnValue(
        createUseRoleReturnFromAuth(createMockAuthContext(null, false)),
      );
    }
  } catch {
    // Modules may not be resolved in some test runners; ignore.
  }
};

export const setupHookMocksIsolation = () => {
  beforeEach(() => {
    resetHookMocks();
  });
  afterEach(() => {
    cleanupHookMocks();
  });
};

export { setupHookMocksIsolation as setupTestIsolation };

// ---------------------------------------------------------------------------
// Usage example (inside a test file):
// ---------------------------------------------------------------------------
/**
 * import { vi } from 'vitest';
 * import { mockScenarios, makeUseAuthMockModule, makeUseRoleMockModule } from '@/tests/utils/hook-mocking-utils';
 *
 * const { authContext, roleReturn } = mockScenarios.superAdmin();
 * vi.mock('@/contexts/AuthContext', () => makeUseAuthMockModule(authContext));
 * vi.mock('@/hooks/useRole', () => makeUseRoleMockModule(roleReturn));
 */
