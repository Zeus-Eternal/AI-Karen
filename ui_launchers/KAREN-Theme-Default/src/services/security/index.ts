/**
 * Security Service
 * 
 * This service consolidates all security-related functionality including:
 * - RBAC (Role-Based Access Control)
 * - Authentication and session management
 * - IP security and MFA management
 * - Security auditing and logging
 * 
 * It uses the canonical enhanced-api-client for all API calls and follows the
 * standard architectural flow: Page → Providers → Hooks → Services → lib → app/api
 */

import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { 
  User, 
  RoleName, 
  Permission, 
  PermissionCheckResult, 
  RoleCheckResult,
  RBACConfig,
  RBACStatistics,
  EvilModeConfig,
  EvilModeSession
} from '@/lib/security/rbac/types';
import { rbacService } from '@/lib/security/rbac/RBACService';
import { securityManager } from '@/lib/security/security-manager';
import { IpSecurityManager } from '@/lib/security/ip-security-manager';
import { MfaManager } from '@/lib/security/mfa-manager';
import { sessionTimeoutManager } from '@/lib/security/session-timeout-manager';
import type { AdminUser } from '@/types/admin';

/**
 * Security Service Class
 * 
 * Centralizes all security operations and provides a unified API for
 * authentication, authorization, and security management.
 */
// Default RBAC configuration
const DEFAULT_RBAC_CONFIG: RBACConfig = {
  enableCache: true,
  cacheTTL: 5 * 60 * 1000, // 5 minutes
  enableDebugLogging: false,
  enableStrictMode: false,
  enableDynamicPermissions: true,
  defaultRole: 'user',
  guestRole: 'readonly',
  enableRoleHierarchy: true,
  conflictResolution: 'first-wins',
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
  requireReauthentication: false,
  auditLevel: 'medium',
  cachePermissions: true
};

export class SecurityService {
  private static instance: SecurityService | null = null;
  private config: RBACConfig;
  private isInitialized = false;
  private initializationPromise: Promise<void> | null = null;
  private securityManager = securityManager;
  private ipSecurityManager: IpSecurityManager;
  private mfaManager: MfaManager;
  private sessionTimeoutManager = sessionTimeoutManager;

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor(config?: Partial<RBACConfig>) {
    this.config = { ...DEFAULT_RBAC_CONFIG, ...config };
    this.ipSecurityManager = new IpSecurityManager();
    this.mfaManager = new MfaManager();
  }

  /**
   * Get the singleton instance of the SecurityService
   * @returns The SecurityService instance
   */
  public static getInstance(): SecurityService {
    if (!SecurityService.instance) {
      SecurityService.instance = new SecurityService();
    }
    return SecurityService.instance;
  }

  /**
   * Initialize the security system
   * @returns A promise that resolves when initialization is complete
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = this.doInitialize();
    return this.initializationPromise;
  }

  /**
   * Perform the actual initialization
   */
  private async doInitialize(): Promise<void> {
    try {
      // Initialize RBAC system
      await rbacService.initialize();

      // Initialize security managers
      // No initialization needed for securityManager and sessionTimeoutManager
      // IpSecurityManager.initialize() is private, so we can't call it directly
      // It will be initialized when needed

      this.isInitialized = true;
    } catch (error) {
      console.error('SecurityService: Failed to initialize:', error);
      throw error;
    }
  }

  /**
   * Authenticate a user with credentials
   * @param username The username
   * @param password The password
   * @returns A promise that resolves with the user data and session
   */
  public async authenticate(username: string, password: string): Promise<{
    user: User;
    token: string;
    refreshToken: string;
    expiresIn: number;
  }> {
    try {
      const response = await enhancedApiClient.post('/api/auth/login', {
        username,
        password
      });

      // Type assertion for the response data
      const responseData = response.data as {
        user: User;
        token: string;
        refreshToken: string;
        expiresIn: number;
      };

      const { user, token, refreshToken, expiresIn } = responseData;

      // Set the current user in the RBAC service
      rbacService.setCurrentUser(user);

      // Create a session with the session timeout manager
      // Convert User to AdminUser type
      const adminUser: AdminUser = {
        ...user,
        user_id: user.id, // Map id to user_id
        tenant_id: (user.metadata as { tenant_id?: string })?.tenant_id || 'default', // Get tenant_id from metadata or use default
        role: (user.roles?.[0] as AdminUser['role']) || 'user', // Use first role or default to 'user'
        is_verified: true,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        failed_login_attempts: 0
      };
      
      await this.sessionTimeoutManager.createSession(
        adminUser,
        token,
        undefined, // ipAddress
        undefined  // userAgent
      );

      return {
        user,
        token,
        refreshToken,
        expiresIn
      };
    } catch (error) {
      console.error('SecurityService: Authentication failed:', error);
      throw error;
    }
  }

  /**
   * Log out the current user
   * @returns A promise that resolves when logout is complete
   */
  public async logout(): Promise<void> {
    try {
      await enhancedApiClient.post('/api/auth/logout');
      
      // Clear the current user in the RBAC service
      rbacService.setCurrentUser(null);
      
      // Clear session timeout
      // Note: Session timeout manager doesn't have a clearSession method
    } catch (error) {
      console.error('SecurityService: Logout failed:', error);
      throw error;
    }
  }

  /**
   * Refresh the authentication token
   * @param refreshToken The refresh token
   * @returns A promise that resolves with the new token data
   */
  public async refreshToken(refreshToken: string): Promise<{
    token: string;
    refreshToken: string;
    expiresIn: number;
  }> {
    try {
      const response = await enhancedApiClient.post('/api/auth/refresh', {
        refreshToken
      });

      // Type assertion for the response data
      const responseData = response.data as {
        token: string;
        refreshToken: string;
        expiresIn: number;
      };

      const { token, refreshToken: newRefreshToken, expiresIn } = responseData;

      // Update session timeout
      // Note: We need to extend the session instead of starting a new one
      // For now, we'll just update the session activity
      if (rbacService.getCurrentUser()) {
        await this.sessionTimeoutManager.updateSessionActivity(token);
      }

      return {
        token,
        refreshToken: newRefreshToken,
        expiresIn
      };
    } catch (error) {
      console.error('SecurityService: Token refresh failed:', error);
      throw error;
    }
  }

  /**
   * Validate the current session
   * @returns A promise that resolves with the validation result
   */
  public async validateSession(): Promise<{
    valid: boolean;
    user?: User;
    expiresAt?: Date;
  }> {
    try {
      const response = await enhancedApiClient.get('/api/auth/validate-session');
      
      // Type assertion for the response data
      const responseData = response.data as {
        valid: boolean;
        user?: User;
        expiresAt?: string;
      };
      
      const { valid, user, expiresAt } = responseData;
      
      if (valid && user) {
        // Set the current user in the RBAC service
        rbacService.setCurrentUser(user);
      }
      
      return {
        valid,
        user,
        expiresAt: expiresAt ? new Date(expiresAt) : undefined
      };
    } catch (error) {
      console.error('SecurityService: Session validation failed:', error);
      return { valid: false };
    }
  }

  /**
   * Check if the current user has a specific permission
   * @param permission The permission to check
   * @returns A PermissionCheckResult object with the result
   */
  public hasPermission(permission: Permission): PermissionCheckResult {
    return rbacService.hasPermission(permission);
  }

  /**
   * Check if the current user has any of the specified permissions
   * @param permissions An array of permissions to check
   * @returns A PermissionCheckResult object with the result
   */
  public hasAnyPermission(permissions: Permission[]): PermissionCheckResult {
    return rbacService.hasAnyPermission(permissions);
  }

  /**
   * Check if the current user has all of the specified permissions
   * @param permissions An array of permissions to check
   * @returns A PermissionCheckResult object with the result
   */
  public hasAllPermissions(permissions: Permission[]): PermissionCheckResult {
    return rbacService.hasAllPermissions(permissions);
  }

  /**
   * Check if the current user has a specific role
   * @param role The role to check
   * @returns A RoleCheckResult object with the result
   */
  public hasRole(role: RoleName): RoleCheckResult {
    return rbacService.hasRole(role);
  }

  /**
   * Check if the current user has any of the specified roles
   * @param roles An array of roles to check
   * @returns A RoleCheckResult object with the result
   */
  public hasAnyRole(roles: RoleName[]): RoleCheckResult {
    return rbacService.hasAnyRole(roles);
  }

  /**
   * Check if the current user has all of the specified roles
   * @param roles An array of roles to check
   * @returns A RoleCheckResult object with the result
   */
  public hasAllRoles(roles: RoleName[]): RoleCheckResult {
    return rbacService.hasAllRoles(roles);
  }

  /**
   * Get all permissions for the current user
   * @returns An array of all permissions for the current user
   */
  public getUserPermissions(): Permission[] {
    return rbacService.getUserPermissions();
  }

  /**
   * Get all roles for the current user
   * @returns An array of all roles for the current user
   */
  public getUserRoles(): RoleName[] {
    return rbacService.getUserRoles();
  }

  /**
   * Get the current user
   * @returns The current user, or null if no user is set
   */
  public getCurrentUser(): User | null {
    return rbacService.getCurrentUser();
  }

  /**
   * Get all available roles
   * @returns An array of all available role names
   */
  public getAllRoles(): RoleName[] {
    return rbacService.getAllRoles();
  }

  /**
   * Get all available permissions
   * @returns An array of all available permissions
   */
  public getAllPermissions(): Permission[] {
    return rbacService.getAllPermissions();
  }

  /**
   * Get all role definitions
   * @returns An object mapping role names to their definitions
   */
  public getAllRoleDefinitions(): Record<RoleName, unknown> {
    return rbacService.getAllRoleDefinitions();
  }

  /**
   * Get the RBAC statistics
   * @returns The RBAC statistics
   */
  public getRBACStatistics(): RBACStatistics {
    return rbacService.getStatistics();
  }

  /**
   * Enable Evil Mode for the current user
   * @param justification The justification for enabling Evil Mode
   * @param timeout The timeout in minutes (optional)
   * @returns A promise that resolves with the Evil Mode session data
   */
  public async enableEvilMode(justification: string, timeout?: number): Promise<EvilModeSession> {
    try {
      const response = await enhancedApiClient.post('/api/auth/evil-mode/enable', {
        justification,
        timeout
      });

      // Type assertion for the response data
      return response.data as EvilModeSession;
    } catch (error) {
      console.error('SecurityService: Failed to enable Evil Mode:', error);
      throw error;
    }
  }

  /**
   * Disable Evil Mode for the current user
   * @returns A promise that resolves when Evil Mode is disabled
   */
  public async disableEvilMode(): Promise<void> {
    try {
      await enhancedApiClient.post('/api/auth/evil-mode/disable');
    } catch (error) {
      console.error('SecurityService: Failed to disable Evil Mode:', error);
      throw error;
    }
  }

  /**
   * Get the current Evil Mode status
   * @returns A promise that resolves with the Evil Mode status
   */
  public async getEvilModeStatus(): Promise<{
    enabled: boolean;
    session?: EvilModeSession;
    config: EvilModeConfig;
  }> {
    try {
      const response = await enhancedApiClient.get('/api/auth/evil-mode/status');
      
      // Type assertion for the response data
      return response.data as {
        enabled: boolean;
        session?: EvilModeSession;
        config: EvilModeConfig;
      };
    } catch (error) {
      console.error('SecurityService: Failed to get Evil Mode status:', error);
      throw error;
    }
  }

  /**
   * Log an Evil Mode action
   * @param action The action performed
   * @param resource The resource affected
   * @param impact The impact of the action
   * @param details Additional details about the action
   * @returns A promise that resolves when the action is logged
   */
  public async logEvilModeAction(
    action: string,
    resource: string,
    impact: string,
    details: Record<string, unknown> = {}
  ): Promise<void> {
    try {
      await enhancedApiClient.post('/api/auth/evil-mode/log-action', {
        action,
        resource,
        impact,
        details
      });
    } catch (error) {
      console.error('SecurityService: Failed to log Evil Mode action:', error);
      throw error;
    }
  }

  /**
   * Set up MFA for the current user
   * @returns A promise that resolves with the MFA setup data
   */
  public async setupMFA(): Promise<{
    secret: string;
    qrCodeUrl: string;
    backupCodes: string[];
  }> {
    try {
      const response = await enhancedApiClient.post('/api/auth/mfa/setup');
      
      // Type assertion for the response data
      return response.data as {
        secret: string;
        qrCodeUrl: string;
        backupCodes: string[];
      };
    } catch (error) {
      console.error('SecurityService: Failed to set up MFA:', error);
      throw error;
    }
  }

  /**
   * Verify and enable MFA for the current user
   * @param token The MFA token
   * @returns A promise that resolves with the verification result
   */
  public async verifyAndEnableMFA(token: string): Promise<{
    success: boolean;
    backupCodes: string[];
  }> {
    try {
      const response = await enhancedApiClient.post('/api/auth/mfa/verify', {
        token
      });
      
      // Type assertion for the response data
      return response.data as {
        success: boolean;
        backupCodes: string[];
      };
    } catch (error) {
      console.error('SecurityService: Failed to verify and enable MFA:', error);
      throw error;
    }
  }

  /**
   * Disable MFA for the current user
   * @param token The MFA token
   * @returns A promise that resolves when MFA is disabled
   */
  public async disableMFA(token: string): Promise<void> {
    try {
      await enhancedApiClient.post('/api/auth/mfa/disable', {
        token
      });
    } catch (error) {
      console.error('SecurityService: Failed to disable MFA:', error);
      throw error;
    }
  }

  /**
   * Validate an MFA token
   * @param token The MFA token
   * @returns A promise that resolves with the validation result
   */
  public async validateMFAToken(token: string): Promise<{
    valid: boolean;
  }> {
    try {
      const response = await enhancedApiClient.post('/api/auth/mfa/validate', {
        token
      });
      
      // Type assertion for the response data
      return response.data as {
        valid: boolean;
      };
    } catch (error) {
      console.error('SecurityService: Failed to validate MFA token:', error);
      throw error;
    }
  }

  /**
   * Get the current user's security settings
   * @returns A promise that resolves with the security settings
   */
  public async getSecuritySettings(): Promise<{
    mfaEnabled: boolean;
    ipRestrictions: string[];
    sessionTimeout: number;
    evilModeConfig: EvilModeConfig;
  }> {
    try {
      const response = await enhancedApiClient.get('/api/auth/security-settings');
      
      // Type assertion for the response data
      return response.data as {
        mfaEnabled: boolean;
        ipRestrictions: string[];
        sessionTimeout: number;
        evilModeConfig: EvilModeConfig;
      };
    } catch (error) {
      console.error('SecurityService: Failed to get security settings:', error);
      throw error;
    }
  }

  /**
   * Update the current user's security settings
   * @param settings The security settings to update
   * @returns A promise that resolves with the updated settings
   */
  public async updateSecuritySettings(settings: {
    mfaEnabled?: boolean;
    ipRestrictions?: string[];
    sessionTimeout?: number;
    evilModeConfig?: Partial<EvilModeConfig>;
  }): Promise<{
    mfaEnabled: boolean;
    ipRestrictions: string[];
    sessionTimeout: number;
    evilModeConfig: EvilModeConfig;
  }> {
    try {
      const response = await enhancedApiClient.put('/api/auth/security-settings', settings);
      
      // Type assertion for the response data
      return response.data as {
        mfaEnabled: boolean;
        ipRestrictions: string[];
        sessionTimeout: number;
        evilModeConfig: EvilModeConfig;
      };
    } catch (error) {
      console.error('SecurityService: Failed to update security settings:', error);
      throw error;
    }
  }

  /**
   * Get the security audit log
   * @param options The options for fetching the audit log
   * @returns A promise that resolves with the audit log
   */
  public async getSecurityAuditLog(options: {
    limit?: number;
    offset?: number;
    startDate?: Date;
    endDate?: Date;
    userId?: string;
    action?: string;
  } = {}): Promise<{
    entries: Array<{
      id: string;
      timestamp: Date;
      userId: string;
      action: string;
      resource: string;
      result: 'SUCCESS' | 'FAILURE';
      ipAddress: string;
      userAgent: string;
      details: Record<string, unknown>;
    }>;
    total: number;
    limit: number;
    offset: number;
  }> {
    try {
      // Build query string manually
      const queryParams = new URLSearchParams();
      if (options.limit !== undefined) queryParams.append('limit', options.limit.toString());
      if (options.offset !== undefined) queryParams.append('offset', options.offset.toString());
      if (options.startDate) queryParams.append('startDate', options.startDate.toISOString());
      if (options.endDate) queryParams.append('endDate', options.endDate.toISOString());
      if (options.userId) queryParams.append('userId', options.userId);
      if (options.action) queryParams.append('action', options.action);
      
      const queryString = queryParams.toString();
      const url = queryString ? `/api/auth/audit-log?${queryString}` : '/api/auth/audit-log';
      
      const response = await enhancedApiClient.get(url);
      
      // Type assertion for the response data
      return response.data as {
        entries: Array<{
          id: string;
          timestamp: Date;
          userId: string;
          action: string;
          resource: string;
          result: 'SUCCESS' | 'FAILURE';
          ipAddress: string;
          userAgent: string;
          details: Record<string, unknown>;
        }>;
        total: number;
        limit: number;
        offset: number;
      };
    } catch (error) {
      console.error('SecurityService: Failed to get security audit log:', error);
      throw error;
    }
  }

  /**
   * Check if an IP address is allowed
   * @param ipAddress The IP address to check
   * @returns A promise that resolves with the check result
   */
  public async isIPAllowed(ipAddress: string): Promise<{
    allowed: boolean;
    reason?: string;
  }> {
    try {
      // Build query string manually
      const queryParams = new URLSearchParams();
      if (ipAddress) queryParams.append('ipAddress', ipAddress);
      
      const queryString = queryParams.toString();
      const url = queryString ? `/api/auth/check-ip?${queryString}` : '/api/auth/check-ip';
      
      const response = await enhancedApiClient.get(url);
      
      // Type assertion for the response data
      return response.data as {
        allowed: boolean;
        reason?: string;
      };
    } catch (error) {
      console.error('SecurityService: Failed to check IP address:', error);
      throw error;
    }
  }

  /**
   * Add an IP address to the allowed list
   * @param ipAddress The IP address to add
   * @param description A description of the IP address
   * @returns A promise that resolves when the IP address is added
   */
  public async addAllowedIP(ipAddress: string, description: string): Promise<void> {
    try {
      await enhancedApiClient.post('/api/auth/allowed-ips', {
        ipAddress,
        description
      });
    } catch (error) {
      console.error('SecurityService: Failed to add allowed IP:', error);
      throw error;
    }
  }

  /**
   * Remove an IP address from the allowed list
   * @param ipAddress The IP address to remove
   * @returns A promise that resolves when the IP address is removed
   */
  public async removeAllowedIP(ipAddress: string): Promise<void> {
    try {
      await enhancedApiClient.delete(`/api/auth/allowed-ips/${ipAddress}`);
    } catch (error) {
      console.error('SecurityService: Failed to remove allowed IP:', error);
      throw error;
    }
  }

  /**
   * Get the list of allowed IP addresses
   * @returns A promise that resolves with the list of allowed IP addresses
   */
  public async getAllowedIPs(): Promise<Array<{
    ipAddress: string;
    description: string;
    addedAt: Date;
    addedBy: string;
  }>> {
    try {
      const response = await enhancedApiClient.get('/api/auth/allowed-ips');
      
      // Type assertion for the response data
      return response.data as Array<{
        ipAddress: string;
        description: string;
        addedAt: Date;
        addedBy: string;
      }>;
    } catch (error) {
      console.error('SecurityService: Failed to get allowed IPs:', error);
      throw error;
    }
  }

  /**
   * Clear all security caches
   */
  public clearCaches(): void {
    rbacService.clearCaches();
    // SecurityManager doesn't have a clearCache method
    // IpSecurityManager doesn't have a clearCache method
    // MfaManager doesn't have a clearCache method
  }

  /**
   * Reset the security system
   * @returns A promise that resolves when reset is complete
   */
  public async reset(): Promise<void> {
    await rbacService.reset();
    // SecurityManager doesn't have a reset method
    // IpSecurityManager doesn't have a reset method
    // MfaManager doesn't have a reset method
    this.sessionTimeoutManager.destroy();
  }
}

// Export the singleton instance
export const securityService = SecurityService.getInstance();
