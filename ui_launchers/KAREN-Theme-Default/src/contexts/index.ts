/**
 * Contexts Index - Production Grade
 *
 * Centralized export hub for all context providers and related utilities.
 */

export { AppProviders } from './AppProviders';
export type { AppProvidersProps } from './AppProviders';

export { AuthProvider, useAuth } from './AuthContext';
export type { LoginCredentials, AuthError, AuthState, AuthProviderProps, AuthContextType, User } from './AuthContext';

export { authStateManager } from './AuthStateManager';
export type { AuthSnapshot, Listener } from './AuthStateManager';

export { ErrorProvider, withErrorProvider, useError, default as Errorprovider } from './ErrorProvider';
export type { ErrorProviderProps, ErrorContextType } from './ErrorProvider';

export { HookProvider, HookContext } from './HookContext';
export { useHooks } from '../hooks/use-hooks';
export type { HookProviderProps } from './HookContext';
export type { HookContextType, HookRegistration, HookResult } from './hook-context';

export { SessionProvider, SessionContext, withSessionProvider, default as Sessionprovider } from './SessionProvider';
export { useSession } from '../hooks/use-session';
export type { SessionProviderProps } from './SessionProvider';
export type { SessionContextType, SessionUser } from './session-context';

