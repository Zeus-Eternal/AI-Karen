/**
 * Security types for the CoPilot frontend.
 * 
 * This file contains TypeScript type definitions for the security system
 * including authentication, authorization, MFA, device verification, and
 * security monitoring.
 */

// Authentication Types
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  roles: string[];
  permissions: string[];
  isActive: boolean;
  isEmailVerified: boolean;
  isMfaEnabled: boolean;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
  profile?: UserProfile;
}

export interface UserProfile {
  avatar?: string;
  bio?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  theme?: string;
  preferences?: Record<string, unknown>;
}

export interface AuthCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
  deviceFingerprint?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  scope?: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastActivity: string;
  sessionTimeout: number;
}

export interface LoginRequest {
  username: string;
  password: string;
  rememberMe?: boolean;
  deviceFingerprint?: string;
  mfaCode?: string;
  mfaMethod?: MfaMethod;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
  requiresMfa: boolean;
  mfaMethods?: MfaMethod[];
  deviceTrusted?: boolean;
  securityEvents?: SecurityEvent[];
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  acceptTerms: boolean;
  subscribeNewsletter?: boolean;
}

export interface RegisterResponse {
  user: User;
  requiresEmailVerification: boolean;
  message: string;
}

// MFA Types
export enum MfaMethod {
  TOTP = 'totp',
  SMS = 'sms',
  EMAIL = 'email',
  BACKUP_CODE = 'backup_code'
}

export interface MfaSetupRequest {
  method: MfaMethod;
  phoneNumber?: string;
  emailAddress?: string;
}

export interface MfaSetupResponse {
  secret?: string;
  qrCode?: string;
  backupCodes?: string[];
  verificationToken: string;
}

export interface MfaVerifyRequest {
  method: MfaMethod;
  code: string;
  verificationToken: string;
}

export interface MfaVerifyResponse {
  success: boolean;
  message: string;
  backupCodesRemaining?: number;
}

export interface MfaStatus {
  isEnabled: boolean;
  methods: MfaMethod[];
  primaryMethod?: MfaMethod;
  backupCodesCount: number;
  lastUsed?: string;
}

// Device Verification Types
export interface DeviceInfo {
  deviceId: string;
  deviceName: string;
  deviceType: string;
  platform: string;
  browser: string;
  browserVersion: string;
  os: string;
  osVersion: string;
  ipAddress: string;
  location?: string;
  isTrusted: boolean;
  trustLevel: DeviceTrustLevel;
  lastSeen: string;
  createdAt: string;
}

export enum DeviceTrustLevel {
  UNKNOWN = 'unknown',
  UNTRUSTED = 'untrusted',
  PENDING = 'pending',
  TRUSTED = 'trusted',
  BLOCKED = 'blocked'
}

export interface DeviceFingerprint {
  canvas: string;
  webgl: string;
  fonts: string[];
  plugins: string[];
  screen: string;
  timezone: string;
  language: string;
  userAgent: string;
}

export interface DeviceVerificationRequest {
  deviceId: string;
  verificationCode?: string;
  trustDuration?: number;
}

export interface DeviceVerificationResponse {
  success: boolean;
  deviceInfo: DeviceInfo;
  message: string;
}

// Security Monitoring Types
export interface SecurityEvent {
  id: string;
  type: SecurityEventType;
  severity: SecuritySeverity;
  title: string;
  description: string;
  userId?: string;
  sessionId?: string;
  deviceId?: string;
  ipAddress?: string;
  location?: string;
  timestamp: string;
  resolved: boolean;
  resolvedAt?: string;
  resolvedBy?: string;
  metadata: Record<string, unknown>;
}

export enum SecurityEventType {
  LOGIN_SUCCESS = 'login_success',
  LOGIN_FAILURE = 'login_failure',
  LOGOUT = 'logout',
  PASSWORD_CHANGE = 'password_change',
  PASSWORD_RESET = 'password_reset',
  MFA_ENABLED = 'mfa_enabled',
  MFA_DISABLED = 'mfa_disabled',
  MFA_VERIFICATION_SUCCESS = 'mfa_verification_success',
  MFA_VERIFICATION_FAILURE = 'mfa_verification_failure',
  DEVICE_TRUSTED = 'device_trusted',
  DEVICE_BLOCKED = 'device_blocked',
  ACCOUNT_LOCKED = 'account_locked',
  ACCOUNT_UNLOCKED = 'account_unlocked',
  SUSPICIOUS_ACTIVITY = 'suspicious_activity',
  THREAT_DETECTED = 'threat_detected',
  PRIVILEGE_ESCALATION = 'privilege_escalation',
  UNAUTHORIZED_ACCESS = 'unauthorized_access',
  DATA_BREACH = 'data_breach'
}

export enum SecuritySeverity {
  INFO = 'info',
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface ThreatIndicator {
  id: string;
  type: ThreatType;
  severity: SecuritySeverity;
  description: string;
  source: string;
  confidence: number;
  firstSeen: string;
  lastSeen: string;
  count: number;
  isActive: boolean;
  metadata: Record<string, unknown>;
}

export enum ThreatType {
  BRUTE_FORCE = 'brute_force',
  CREDENTIAL_STUFFING = 'credential_stuffing',
  SQL_INJECTION = 'sql_injection',
  XSS = 'xss',
  CSRF = 'csrf',
  DIRECTORY_TRAVERSAL = 'directory_traversal',
  COMMAND_INJECTION = 'command_injection',
  DDOS = 'ddos',
  MALICIOUS_IP = 'malicious_ip',
  SUSPICIOUS_USER_AGENT = 'suspicious_user_agent',
  ANOMALOUS_BEHAVIOR = 'anomalous_behavior'
}

// RBAC Types
export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface UserRole {
  userId: string;
  roleId: string;
  assignedAt: string;
  assignedBy: string;
  expiresAt?: string;
  isActive: boolean;
}

// Security Policy Types
export interface SecurityPolicy {
  id: string;
  name: string;
  description: string;
  type: PolicyType;
  status: PolicyStatus;
  rules: PolicyRule[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
}

export enum PolicyType {
  PASSWORD = 'password',
  SESSION = 'session',
  MFA = 'mfa',
  DEVICE = 'device',
  ACCESS = 'access',
  DATA = 'data',
  ENCRYPTION = 'encryption',
  AUDIT = 'audit'
}

export enum PolicyStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DRAFT = 'draft',
  ARCHIVED = 'archived'
}

export interface PolicyRule {
  id: string;
  name: string;
  description: string;
  conditions: PolicyCondition[];
  actions: PolicyAction[];
  isActive: boolean;
  priority: number;
}

export interface PolicyCondition {
  field: string;
  operator: string;
  value: unknown;
  logicalOperator?: 'AND' | 'OR';
}

export interface PolicyAction {
  type: PolicyActionType;
  parameters: Record<string, unknown>;
}

export enum PolicyActionType {
  ALLOW = 'allow',
  DENY = 'deny',
  REQUIRE_MFA = 'require_mfa',
  LOG = 'log',
  ALERT = 'alert',
  BLOCK = 'block',
  REDIRECT = 'redirect',
  NOTIFY = 'notify'
}

// Vulnerability Scanning Types
export interface VulnerabilityScan {
  id: string;
  name: string;
  description: string;
  targetSystem: string;
  status: ScanStatus;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  findings: VulnerabilityFinding[];
  testResults: Record<string, unknown>;
  errorMessage?: string;
  createdBy: string;
}

export enum ScanStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout'
}

export interface VulnerabilityFinding {
  id: string;
  scanId: string;
  category: VulnerabilityCategory;
  severity: VulnerabilitySeverity;
  title: string;
  description: string;
  affectedComponent: string;
  affectedEndpoint?: string;
  affectedParameter?: string;
  payloadSample?: string;
  remediation?: string;
  references: string[];
  cvssScore?: number;
  cvssVector?: string;
  discoveredAt: string;
  confirmedAt?: string;
  fixedAt?: string;
  metadata: Record<string, unknown>;
}

export enum VulnerabilityCategory {
  INJECTION = 'injection',
  XSS = 'xss',
  CSRF = 'csrf',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  SESSION_MANAGEMENT = 'session_management',
  CONFIGURATION = 'configuration',
  CRYPTOGRAPHY = 'cryptography',
  NETWORK = 'network',
  INPUT_VALIDATION = 'input_validation',
  BUSINESS_LOGIC = 'business_logic',
  DENIAL_OF_SERVICE = 'denial_of_service',
  INFORMATION_DISCLOSURE = 'information_disclosure',
  PRIVILEGE_ESCALATION = 'privilege_escalation'
}

export enum VulnerabilitySeverity {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info'
}

// API Response Types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  metadata?: Record<string, unknown>;
}

export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// Security Configuration Types
export interface SecurityConfig {
  passwordPolicy: PasswordPolicy;
  sessionPolicy: SessionPolicy;
  mfaPolicy: MfaPolicy;
  devicePolicy: DevicePolicy;
  monitoringPolicy: MonitoringPolicy;
}

export interface PasswordPolicy {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  preventReuse: number;
  expiryDays: number;
  lockoutThreshold: number;
  lockoutDuration: number;
}

export interface SessionPolicy {
  timeoutMinutes: number;
  maxConcurrentSessions: number;
  requireReauth: boolean;
  reauthIntervalMinutes: number;
  secureCookies: boolean;
  sameSitePolicy: string;
}

export interface MfaPolicy {
  required: boolean;
  methods: MfaMethod[];
  gracePeriodDays: number;
  rememberDeviceDays: number;
  backupCodesCount: number;
}

export interface DevicePolicy {
  maxDevices: number;
  trustDurationDays: number;
  requireVerification: boolean;
  blockSuspiciousDevices: boolean;
}

export interface MonitoringPolicy {
  enableLogging: boolean;
  enableAlerts: boolean;
  alertThresholdSeverity: SecuritySeverity;
  retentionDays: number;
}

// Form Types
export interface LoginForm {
  username: string;
  password: string;
  rememberMe: boolean;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  acceptTerms: boolean;
}

export interface MfaForm {
  code: string;
  method: MfaMethod;
  rememberDevice: boolean;
}

export interface PasswordResetForm {
  email: string;
}

export interface PasswordChangeForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ProfileForm {
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  bio?: string;
  timezone?: string;
  language?: string;
  theme?: string;
}

// Navigation and Route Types
export interface ProtectedRoute {
  path: string;
  component: React.ComponentType;
  permissions?: string[];
  roles?: string[];
  requireAuth?: boolean;
  requireMfa?: boolean;
}

export interface SecurityContext {
  auth: AuthState;
  user: User | null;
  permissions: string[];
  roles: string[];
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  login: (credentials: LoginRequest) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  register: (data: RegisterRequest) => Promise<RegisterResponse>;
  refreshToken: () => Promise<AuthTokens>;
  changePassword: (data: PasswordChangeForm) => Promise<void>;
  updateProfile: (data: ProfileForm) => Promise<User>;
  enableMfa: (method: MfaMethod) => Promise<MfaSetupResponse>;
  disableMfa: () => Promise<void>;
  verifyMfa: (data: MfaVerifyRequest) => Promise<MfaVerifyResponse>;
  trustDevice: (deviceId: string) => Promise<void>;
  revokeDevice: (deviceId: string) => Promise<void>;
  getSecurityEvents: () => Promise<SecurityEvent[]>;
  getDevices: () => Promise<DeviceInfo[]>;
  getVulnerabilityScans: () => Promise<VulnerabilityScan[]>;
}
