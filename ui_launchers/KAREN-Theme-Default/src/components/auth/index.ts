/**
 * Authentication Component Exports
 *
 * Central barrel export for authentication-related components, route guards,
 * session boundaries, and user/auth UI elements.
 */

// -------------------------------------
// Route Guards
// -------------------------------------
export { ProtectedRoute } from './ProtectedRoute';
export type { ProtectedRouteProps } from './ProtectedRoute';

export { AdminRoute } from './AdminRoute';
export type { AdminRouteProps } from './AdminRoute';

export { SuperAdminRoute } from './SuperAdminRoute';
export type { SuperAdminRouteProps } from './SuperAdminRoute';

// -------------------------------------
// Session Management
// -------------------------------------
export { SessionErrorBoundary, withSessionErrorBoundary } from './SessionErrorBoundary';
export type {
  SessionErrorBoundaryProps,
  SessionErrorBoundaryState,
} from './SessionErrorBoundary';

export { TokenStatus } from './TokenStatus';
export type { SessionMode, SessionInfo } from './TokenStatus';

// -------------------------------------
// User Components
// -------------------------------------
export { default as LoginForm } from './LoginForm';
export type { LoginFormProps } from './LoginForm';

export { UserProfile } from './UserProfile';
export type { UserProfileProps } from './UserProfile';

export { default as AuthHeader } from './AuthHeader';

// -------------------------------------
// Setup (optional subdirectory)
// -------------------------------------
// export * from './setup';
