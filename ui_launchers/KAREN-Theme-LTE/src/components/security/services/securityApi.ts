/**
 * Security API Service for the CoPilot frontend.
 * 
 * This service handles all security-related API calls including authentication,
 * authorization, MFA, device verification, and security monitoring.
 */

import { 
  ApiResponse, 
  AuthTokens, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  RegisterResponse,
  MfaSetupRequest,
  MfaSetupResponse,
  MfaVerifyRequest,
  MfaVerifyResponse,
  MfaStatus,
  DeviceInfo,
  DeviceVerificationRequest,
  DeviceVerificationResponse,
  SecurityEvent,
  VulnerabilityScan,
  PasswordChangeForm,
  ProfileForm,
  User,
  PaginatedResponse,
  VulnerabilityFinding,
  SecurityPolicy,
  Role,
  Permission
} from '../types';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = 'v1';
const SECURITY_API_BASE = `${API_BASE_URL}/api/${API_VERSION}/security`;

// Default headers
const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
};

// Error handling
class SecurityApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'SecurityApiError';
  }
}

// Request interceptor
const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = { ...DEFAULT_HEADERS };
  
  // Add auth token if available
  if (typeof window !== 'undefined') {
    const tokens = localStorage.getItem('auth_tokens');
    if (tokens) {
      try {
        const { accessToken } = JSON.parse(tokens);
        headers['Authorization'] = `Bearer ${accessToken}`;
      } catch (error) {
        console.error('Error parsing auth tokens:', error);
      }
    }
  }
  
  return headers;
};

// Response interceptor
const handleResponse = async <T>(response: Response): Promise<ApiResponse<T>> => {
  const contentType = response.headers.get('content-type');
  const isJson = contentType?.includes('application/json');
  
  let data: unknown;
  try {
    data = isJson ? await response.json() : await response.text();
  } catch (error) {
    throw new SecurityApiError('Failed to parse response', response.status);
  }
  
  if (!response.ok) {
    const message = ((data as Record<string, unknown>)?.error || (data as Record<string, unknown>)?.message || response.statusText || 'Unknown error') as string;
    throw new SecurityApiError(message, response.status, (data as Record<string, unknown>)?.code as string, (data as Record<string, unknown>)?.details as Record<string, unknown>);
  }
  
  return {
    success: true,
    data: data as T,
    message: (data as Record<string, unknown>)?.message as string | undefined,
    metadata: (data as Record<string, unknown>)?.metadata as Record<string, unknown> | undefined,
  };
};

// Generic request function
const request = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  const url = endpoint.startsWith('http') ? endpoint : `${SECURITY_API_BASE}${endpoint}`;
  const headers = { ...getAuthHeaders(), ...options.headers };
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Include cookies for session management
    });
    
    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof SecurityApiError) {
      throw error;
    }
    throw new SecurityApiError('Network error occurred');
  }
};

// Authentication API
export const authApi = {
  /**
   * Login with credentials
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<RegisterResponse>> {
    return request<RegisterResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  /**
   * Logout user
   */
  async logout(): Promise<ApiResponse<void>> {
    return request<void>('/auth/logout', {
      method: 'POST',
    });
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<AuthTokens>> {
    return request<AuthTokens>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refreshToken }),
    });
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    return request<User>('/auth/me');
  },

  /**
   * Update user profile
   */
  async updateProfile(profileData: ProfileForm): Promise<ApiResponse<User>> {
    return request<User>('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },

  /**
   * Change password
   */
  async changePassword(passwordData: PasswordChangeForm): Promise<ApiResponse<void>> {
    return request<void>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<ApiResponse<void>> {
    return request<void>('/auth/request-password-reset', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<ApiResponse<void>> {
    return request<void>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, newPassword }),
    });
  },

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<ApiResponse<void>> {
    return request<void>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },
};

// MFA API
export const mfaApi = {
  /**
   * Get MFA status
   */
  async getMfaStatus(): Promise<ApiResponse<MfaStatus>> {
    return request<MfaStatus>('/mfa/status');
  },

  /**
   * Setup MFA
   */
  async setupMfa(setupData: MfaSetupRequest): Promise<ApiResponse<MfaSetupResponse>> {
    return request<MfaSetupResponse>('/mfa/setup', {
      method: 'POST',
      body: JSON.stringify(setupData),
    });
  },

  /**
   * Verify MFA setup
   */
  async verifyMfaSetup(verifyData: MfaVerifyRequest): Promise<ApiResponse<MfaVerifyResponse>> {
    return request<MfaVerifyResponse>('/mfa/verify-setup', {
      method: 'POST',
      body: JSON.stringify(verifyData),
    });
  },

  /**
   * Disable MFA
   */
  async disableMfa(code: string): Promise<ApiResponse<void>> {
    return request<void>('/mfa/disable', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  },

  /**
   * Generate new backup codes
   */
  async generateBackupCodes(): Promise<ApiResponse<string[]>> {
    return request<string[]>('/mfa/backup-codes/generate', {
      method: 'POST',
    });
  },

  /**
   * Verify MFA code
   */
  async verifyMfaCode(verifyData: MfaVerifyRequest): Promise<ApiResponse<MfaVerifyResponse>> {
    return request<MfaVerifyResponse>('/mfa/verify', {
      method: 'POST',
      body: JSON.stringify(verifyData),
    });
  },
};

// Device Verification API
export const deviceApi = {
  /**
   * Get user devices
   */
  async getDevices(): Promise<ApiResponse<DeviceInfo[]>> {
    return request<DeviceInfo[]>('/devices');
  },

  /**
   * Get device by ID
   */
  async getDevice(deviceId: string): Promise<ApiResponse<DeviceInfo>> {
    return request<DeviceInfo>(`/devices/${deviceId}`);
  },

  /**
   * Trust device
   */
  async trustDevice(deviceId: string, trustDuration?: number): Promise<ApiResponse<void>> {
    return request<void>(`/devices/${deviceId}/trust`, {
      method: 'POST',
      body: JSON.stringify({ trustDuration }),
    });
  },

  /**
   * Revoke device
   */
  async revokeDevice(deviceId: string): Promise<ApiResponse<void>> {
    return request<void>(`/devices/${deviceId}/revoke`, {
      method: 'DELETE',
    });
  },

  /**
   * Block device
   */
  async blockDevice(deviceId: string): Promise<ApiResponse<void>> {
    return request<void>(`/devices/${deviceId}/block`, {
      method: 'POST',
    });
  },

  /**
   * Verify device
   */
  async verifyDevice(verificationData: DeviceVerificationRequest): Promise<ApiResponse<DeviceVerificationResponse>> {
    return request<DeviceVerificationResponse>('/devices/verify', {
      method: 'POST',
      body: JSON.stringify(verificationData),
    });
  },

  /**
   * Get device fingerprint
   */
  async getDeviceFingerprint(): Promise<ApiResponse<string>> {
    return request<string>('/devices/fingerprint');
  },
};

// Security Monitoring API
export const monitoringApi = {
  /**
   * Get security events
   */
  async getSecurityEvents(params?: {
    page?: number;
    pageSize?: number;
    severity?: string;
    type?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<ApiResponse<PaginatedResponse<SecurityEvent>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const query = searchParams.toString();
    return request<PaginatedResponse<SecurityEvent>>(`/monitoring/events${query ? `?${query}` : ''}`);
  },

  /**
   * Get security event by ID
   */
  async getSecurityEvent(eventId: string): Promise<ApiResponse<SecurityEvent>> {
    return request<SecurityEvent>(`/monitoring/events/${eventId}`);
  },

  /**
   * Resolve security event
   */
  async resolveSecurityEvent(eventId: string, resolution?: string): Promise<ApiResponse<void>> {
    return request<void>(`/monitoring/events/${eventId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution }),
    });
  },

  /**
   * Get threat indicators
   */
  async getThreatIndicators(params?: {
    page?: number;
    pageSize?: number;
    type?: string;
    severity?: string;
    isActive?: boolean;
  }): Promise<ApiResponse<PaginatedResponse<unknown>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const query = searchParams.toString();
    return request<PaginatedResponse<unknown>>(`/monitoring/threats${query ? `?${query}` : ''}`);
  },

  /**
   * Get security statistics
   */
  async getSecurityStatistics(): Promise<ApiResponse<Record<string, unknown>>> {
    return request<Record<string, unknown>>('/monitoring/statistics');
  },
};

// Vulnerability Scanning API
export const vulnerabilityApi = {
  /**
   * Get vulnerability scans
   */
  async getVulnerabilityScans(params?: {
    page?: number;
    pageSize?: number;
    status?: string;
    targetSystem?: string;
  }): Promise<ApiResponse<PaginatedResponse<VulnerabilityScan>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const query = searchParams.toString();
    return request<PaginatedResponse<VulnerabilityScan>>(`/vulnerability/scans${query ? `?${query}` : ''}`);
  },

  /**
   * Get vulnerability scan by ID
   */
  async getVulnerabilityScan(scanId: string): Promise<ApiResponse<VulnerabilityScan>> {
    return request<VulnerabilityScan>(`/vulnerability/scans/${scanId}`);
  },

  /**
   * Run vulnerability scan
   */
  async runVulnerabilityScan(data: {
    targetSystem: string;
    testSuiteIds?: string[];
    customConfig?: Record<string, unknown>;
  }): Promise<ApiResponse<VulnerabilityScan>> {
    return request<VulnerabilityScan>('/vulnerability/scans', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get vulnerability findings
   */
  async getVulnerabilityFindings(params?: {
    page?: number;
    pageSize?: number;
    scanId?: string;
    severity?: string;
    category?: string;
    resolved?: boolean;
  }): Promise<ApiResponse<PaginatedResponse<VulnerabilityFinding>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const query = searchParams.toString();
    return request<PaginatedResponse<VulnerabilityFinding>>(`/vulnerability/findings${query ? `?${query}` : ''}`);
  },

  /**
   * Get vulnerability finding by ID
   */
  async getVulnerabilityFinding(findingId: string): Promise<ApiResponse<VulnerabilityFinding>> {
    return request<VulnerabilityFinding>(`/vulnerability/findings/${findingId}`);
  },

  /**
   * Mark vulnerability finding as resolved
   */
  async resolveVulnerabilityFinding(findingId: string, resolution?: string): Promise<ApiResponse<void>> {
    return request<void>(`/vulnerability/findings/${findingId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution }),
    });
  },
};

// RBAC API
export const rbacApi = {
  /**
   * Get user roles
   */
  async getUserRoles(userId?: string): Promise<ApiResponse<Role[]>> {
    const endpoint = userId ? `/rbac/users/${userId}/roles` : '/rbac/me/roles';
    return request<Role[]>(endpoint);
  },

  /**
   * Get user permissions
   */
  async getUserPermissions(userId?: string): Promise<ApiResponse<Permission[]>> {
    const endpoint = userId ? `/rbac/users/${userId}/permissions` : '/rbac/me/permissions';
    return request<Permission[]>(endpoint);
  },

  /**
   * Get all roles
   */
  async getRoles(): Promise<ApiResponse<Role[]>> {
    return request<Role[]>('/rbac/roles');
  },

  /**
   * Get role by ID
   */
  async getRole(roleId: string): Promise<ApiResponse<Role>> {
    return request<Role>(`/rbac/roles/${roleId}`);
  },

  /**
   * Get all permissions
   */
  async getPermissions(): Promise<ApiResponse<Permission[]>> {
    return request<Permission[]>('/rbac/permissions');
  },

  /**
   * Check permission
   */
  async checkPermission(permission: string, resource?: string, action?: string): Promise<ApiResponse<boolean>> {
    const params = new URLSearchParams();
    if (resource) params.append('resource', resource);
    if (action) params.append('action', action);
    
    return request<boolean>(`/rbac/check/${permission}${params.toString() ? `?${params.toString()}` : ''}`);
  },

  /**
   * Check role
   */
  async checkRole(role: string): Promise<ApiResponse<boolean>> {
    return request<boolean>(`/rbac/check-role/${role}`);
  },
};

// Security Policy API
export const policyApi = {
  /**
   * Get security policies
   */
  async getSecurityPolicies(): Promise<ApiResponse<SecurityPolicy[]>> {
    return request<SecurityPolicy[]>('/policies');
  },

  /**
   * Get security policy by ID
   */
  async getSecurityPolicy(policyId: string): Promise<ApiResponse<SecurityPolicy>> {
    return request<SecurityPolicy>(`/policies/${policyId}`);
  },

  /**
   * Create security policy
   */
  async createSecurityPolicy(policyData: Partial<SecurityPolicy>): Promise<ApiResponse<SecurityPolicy>> {
    return request<SecurityPolicy>('/policies', {
      method: 'POST',
      body: JSON.stringify(policyData),
    });
  },

  /**
   * Update security policy
   */
  async updateSecurityPolicy(policyId: string, policyData: Partial<SecurityPolicy>): Promise<ApiResponse<SecurityPolicy>> {
    return request<SecurityPolicy>(`/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify(policyData),
    });
  },

  /**
   * Delete security policy
   */
  async deleteSecurityPolicy(policyId: string): Promise<ApiResponse<void>> {
    return request<void>(`/policies/${policyId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Evaluate security policy
   */
  async evaluateSecurityPolicy(policyId: string, context: Record<string, unknown>): Promise<ApiResponse<unknown>> {
    return request<unknown>(`/policies/${policyId}/evaluate`, {
      method: 'POST',
      body: JSON.stringify({ context }),
    });
  },
};

// Export all APIs
export const securityApi = {
  auth: authApi,
  mfa: mfaApi,
  device: deviceApi,
  monitoring: monitoringApi,
  vulnerability: vulnerabilityApi,
  rbac: rbacApi,
  policy: policyApi,
};

// Export error class
export { SecurityApiError };
