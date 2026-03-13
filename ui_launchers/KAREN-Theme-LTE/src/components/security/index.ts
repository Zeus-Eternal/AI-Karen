/**
 * Security Components Index for the CoPilot frontend.
 * 
 * This file exports all security-related components, services, and utilities
 * for easy importing throughout the application.
 */

// Types
export * from './types';

// Services
export * from './services/securityApi';

// Context
export { SecurityProvider, SecurityContext, useSecurity } from './contexts/SecurityContext';

// Components
export {
  ProtectedRoute,
  withProtection,
  PermissionGuard,
  RoleGuard,
  MfaGuard,
  AuthGuard,
  GuestGuard,
  DefaultLoadingComponent,
  DefaultErrorComponent,
} from './components/ProtectedRoute';

// Utils
export { SecureStorage, secureStorage, storageUtils } from './utils/secureStorage';

// Re-export commonly used items for convenience
export type {
  User,
  AuthState,
  AuthTokens,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  MfaMethod,
  MfaStatus,
  DeviceInfo,
  SecurityEvent,
  VulnerabilityScan,
  PasswordChangeForm,
  ProfileForm,
  SecurityContext as ISecurityContext,
} from './types';

export {
  securityApi,
  authApi,
  mfaApi,
  deviceApi,
  monitoringApi,
  vulnerabilityApi,
  rbacApi,
  policyApi,
  SecurityApiError,
} from './services/securityApi';