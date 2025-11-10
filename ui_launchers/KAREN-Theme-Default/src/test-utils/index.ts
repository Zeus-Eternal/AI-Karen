/**
 * Test Utilities Index - Production Grade
 *
 * Centralized export hub for all testing utilities.
 * Organizes test helpers, mocks, and setup functions.
 */

// ============================================================================
// Authentication Testing
// ============================================================================

export { TEST_CREDENTIALS, testDatabaseConnectivity, testDatabaseAuthentication, testAuthenticationWithDatabaseValidation, validateTestCredentials, createTestSession, cleanupTestSession, summarizeAuth, DatabaseAuthTestSuite } from './auth-test-utils';
export type { TestCredentials, DatabaseConnectivityResult, AuthenticationTestResult } from './auth-test-utils';

// ============================================================================
// Hook Mocking
// ============================================================================

export {
  makeUseAuthMockModule,
  makeUseRoleMockModule,
  setupUseAuthMock,
  setupUseRoleMock,
  createUseRoleReturnFromAuth,
  setupAuthAndRoleMocks,
  mockScenarios,
  createMockUseAuth,
  createMockUseRole,
  createRealisticMockAuth,
  resetHookMocks,
  cleanupHookMocks,
  setupHookMocksIsolation,
  setupHookMocksIsolation as setupHookTestIsolation,
  setupConsistentMocks,
  validateMockSetup,
  debugMockState,
  mockAuthForTest,
  mockAuthWithUser,
  createTestMocks,
  resetToDefaultMocks,
  setupGlobalMocks,
} from './hook-mocks';

// ============================================================================
// Router Mocking
// ============================================================================

export { mockNextNavigationModule, installWindowLocationMock, restoreWindowLocationMock, resetRouterMocks, routerTestState } from './router-mocks';
export type { MockRouter } from './router-mocks';

// ============================================================================
// Test Providers & Rendering
// ============================================================================

export { mockSuperAdminUser, mockAdminUser, mockRegularUser, mockUnauthenticatedUser, mockUserWithMultipleRoles, mockInactiveUser, mockUserWithCustomPermissions, createMockAuthContext, TestAuthProvider, renderWithProviders, mockUseAuth, mockUseAuthHook, mockSuperAdminAuth, mockAdminAuth, mockUserAuth, mockUnauthenticatedAuth, setupAuthMock, setupAuthMockWithScenario, setupRoleMock, setupComprehensiveAuthMocks, createMockImplementations, createSuperAdminAuthContext, createAdminAuthContext, createUserAuthContext, createUnauthenticatedAuthContext, createMultiRoleAuthContext, createCustomPermissionAuthContext, createCustomAuthContext, createAuthErrorContext, createLoadingAuthContext, renderWithSuperAdmin, renderWithAdmin, renderWithUser, renderWithUnauthenticated, renderWithCustomAuth, renderWithAuthError, mockSessionFunctions, resetAllMocks, cleanupTestEnvironment, authTestScenarios, createAuthContextFromScenario, renderWithAuthScenario, runAuthScenarioTests, createPermissionTestMatrix, testPermissionMatrix, createTestAuthContext, createTestUser, createTestSuperAdmin, createTestAdmin, validateAuthContext, validateUser, createTestCredentials, createTestCredentialsWithMFA, createSimpleMockAuth, createSimpleMockRole, mockUIComponents } from './test-providers';
export type { AuthTestScenario } from './test-providers';

// ============================================================================
// Test Setup & Environment
// ============================================================================

export { setupTestEnvironment, setupTestIsolation, setupCompleteTestEnvironment, setupFetchMock, setupLocationMock, setupRouterMock, setupAuthTestEnvironment, waitForAsync, flushPromises, setupTimerMocks, mockErrorBoundary, cleanupTestData, setupIntersectionObserverMock, setupResizeObserverMock, setupComponentTestEnvironment, validateTestEnvironment, debugTestEnvironment } from './test-setup';
