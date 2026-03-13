import { z } from 'zod';

// User interface for authentication
export interface User {
  userId: string;
  email: string;
  roles: string[];
  tenantId?: string;
  role?: string;
  permissions?: string[];
  profile?: {
    firstName?: string;
    lastName?: string;
    avatar?: string;
  };
}

// Authentication state interface
export interface AuthState {
  isLoading: boolean;
  error: string | null;
  isRefreshing: boolean;
  lastActivity: Date | null;
}

// Login credentials interface
export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

// JWT Payload interface
export interface JWTPayload {
  userId: string;
  email: string;
  roles: string[];
  iat?: number;
  exp?: number;
}

// Token response interface
export interface TokenResponse {
  success: boolean;
  token?: string;
  user?: User;
  error?: string;
}

// Auth response interface (with token property)
export interface AuthResponse {
  success: boolean;
  token?: string;
  user?: User;
  error?: string;
}

// API Response interfaces
export interface AuthResponse {
  success: boolean;
  token?: string;
  userId?: string;
  user?: User;
  error?: string;
}

export interface UserDataResponse {
  userId: string;
  submissionId: string;
  submissionTimestamp: string;
}

// Validation schemas using Zod
export const loginSchema = z.object({
  email: z.string().email('Invalid email address').min(1, 'Email is required'),
  password: z.string().min(1, 'Password is required'),
  totp_code: z.string().optional(),
});

export const userSchema = z.object({
  userId: z.string().min(1, 'User ID is required'),
  email: z.string().email('Invalid email address'),
  roles: z.array(z.string()).default([]),
  tenantId: z.string().optional(),
  role: z.string().optional(),
  permissions: z.array(z.string()).optional(),
  profile: z.object({
    firstName: z.string().optional(),
    lastName: z.string().optional(),
    avatar: z.string().optional(),
  }).optional(),
});

export const tokenResponseSchema = z.object({
  success: z.boolean(),
  token: z.string().optional(),
  user: userSchema.optional(),
  error: z.string().optional(),
});

export const authResponseSchema = z.object({
  success: z.boolean(),
  userId: z.string().optional(),
  user: userSchema.optional(),
  error: z.string().optional(),
});

export const userDataResponseSchema = z.object({
  userId: z.string(),
  submissionId: z.string().uuid('Invalid submission ID format'),
  submissionTimestamp: z.string().datetime('Invalid timestamp format'),
});

// Type guards for runtime validation
export function isValidLoginCredentials(data: unknown): data is LoginCredentials {
  return loginSchema.safeParse(data).success;
}

export function isValidUser(data: unknown): data is User {
  return userSchema.safeParse(data).success;
}

export function isValidTokenResponse(data: unknown): data is TokenResponse {
  return tokenResponseSchema.safeParse(data).success;
}

export function isValidAuthResponse(data: unknown): data is AuthResponse {
  return authResponseSchema.safeParse(data).success;
}

export function isValidUserDataResponse(data: unknown): data is UserDataResponse {
  return userDataResponseSchema.safeParse(data).success;
}

// Error types
export class AuthError extends Error {
  constructor(
    message: string,
    public code?: string,
    public statusCode?: number
  ) {
    super(message);
    this.name = 'AuthError';
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public field?: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Role and permission utilities
export const ROLES = {
  USER: 'user',
  ADMIN: 'admin',
  SUPER_ADMIN: 'super_admin',
} as const;

export const PERMISSIONS = {
  READ: 'read',
  WRITE: 'write',
  DELETE: 'delete',
  ADMIN: 'admin',
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];
export type Permission = typeof PERMISSIONS[keyof typeof PERMISSIONS];