/**
 * Security Module Index - Production Grade
 *
 * Centralized export hub for security utilities and types.
 */

export { enhancedAuthMiddleware, EnhancedAuthMiddleware } from './enhanced-auth-middleware';
export type { AuthenticationResult, EnhancedAuthContext } from './enhanced-auth-middleware';

export { WhitelistConflictError, IpSecurityError, getIPSecurityManager, IpSecurityManager, InvalidIpAddressError } from './ip-security-manager';
export type { IpAccessRecord, IpWhitelistEntry, IpSecurityConfig, Bucket, IpSecurityResult } from './ip-security-manager';

export { MfaManager, mfaManager } from './mfa-manager';
export type { MfaVerificationResult, MfaSetupData, MfaStatus } from './mfa-manager';

export { securityManager, SECURITY_CONFIG, SecurityManager } from './security-manager';
export type { AttemptRec } from './security-manager';

export { sessionTimeoutManager, SessionTimeoutManager } from './session-timeout-manager';
export { default as sessionTimeoutManagerSingleton } from './session-timeout-manager';
export type { RoleKey, SessionTimeoutConfig, SessionStatus, ConcurrentSessionSummary } from './session-timeout-manager';

