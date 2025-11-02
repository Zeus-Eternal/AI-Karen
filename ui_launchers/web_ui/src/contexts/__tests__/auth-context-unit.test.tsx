/**
 * Unit tests for AuthContext
 * 
 * Tests the simplified authentication context implementation
 * Requirements: 1.1, 1.3, 4.1, 4.2, 4.5
 */

import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { AuthProvider, useAuth } from '@/contexts/AuthContext';

// Mock session functions
vi.mock('@/lib/auth/session', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  validateSession: vi.fn(),
  hasSessionCookie: vi.fn(),
  getCurrentUser: vi.fn(),
}));


  login as sessionLogin,
  logout as sessionLogout,
  validateSession, 
  hasSessionCookie,
  getCurrentUser 
import { } from '@/lib/auth/session';

const mockLogin = sessionLogin as ReturnType<typeof vi.fn>;
const mockLogout = sessionLogout as ReturnType<typeof vi.fn>;
const mockValidateSession = validateSession as ReturnType<typeof vi.fn>;
const mockHasSessionCookie = hasSessionCookie as ReturnType<typeof vi.fn>;
const mockGetCurrentUser = getCurrentUser as ReturnType<typeof vi.fn>;

// Mock window.location
const mockLocation = {
  href: '',
};
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,

// Test component to access auth context
const TestComponent: React.FC = () => {
  const { user, isAuthenticated, login, logout, checkAuth } = useAuth();
  
  return (
    <div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="user-email">{user?.email || 'null'}</div>
      <div data-testid="user-id">{user?.user_id || 'null'}</div>
      <div data-testid="user-roles">{user?.roles.join(',') || 'null'}</div>
      <button 
        data-testid="login-btn" 
        onClick={() => login({ email: 'test@example.com', password: 'password123' })}
      >
      </button>
      <button data-testid="logout-btn" onClick={logout}>
      </button>
      <button data-testid="check-auth-btn" onClick={() => checkAuth()}>
      </button>
    </div>
  );
};

describe('AuthContext Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation.href = '';
    
    // Default mock implementations
    mockHasSessionCookie.mockReturnValue(false);
    mockValidateSession.mockResolvedValue(false);
    mockGetCurrentUser.mockReturnValue(null);
    mockLogin.mockResolvedValue(undefined);
    mockLogout.mockResolvedValue(undefined);

  afterEach(() => {
    vi.clearAllMocks();

  describe('Initial State', () => {
    it('should initialize with unauthenticated state', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('user-email')).toHaveTextContent('null');
      expect(screen.getByTestId('user-id')).toHaveTextContent('null');
      expect(screen.getByTestId('user-roles')).toHaveTextContent('null');

    it('should check authentication on mount', async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockHasSessionCookie).toHaveBeenCalledTimes(1);


    it('should restore authentication state if valid session exists', async () => {
      const mockUserData = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user', 'admin'],
        tenantId: 'tenant123',
      };

      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue(mockUserData);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
        expect(screen.getByTestId('user-id')).toHaveTextContent('user123');
        expect(screen.getByTestId('user-roles')).toHaveTextContent('user,admin');



  describe('Login Method', () => {
    it('should successfully login with valid credentials', async () => {
      const mockUserData = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      mockLogin.mockResolvedValueOnce(undefined);
      mockGetCurrentUser.mockReturnValue(mockUserData);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Initially not authenticated
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');

      // Trigger login
      await act(async () => {
        screen.getByTestId('login-btn').click();

      // Should be authenticated after login
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
        expect(screen.getByTestId('user-id')).toHaveTextContent('user123');
        expect(screen.getByTestId('user-roles')).toHaveTextContent('user');

      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123', undefined);

    it('should handle login failure and clear state', async () => {
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger login
      await act(async () => {
        screen.getByTestId('login-btn').click();

      // Should remain unauthenticated
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('null');
        expect(screen.getByTestId('user-id')).toHaveTextContent('null');
        expect(screen.getByTestId('user-roles')).toHaveTextContent('null');


    it('should clear state if user data is not available after login', async () => {
      mockLogin.mockResolvedValueOnce(undefined);
      mockGetCurrentUser.mockReturnValue(null); // No user data

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger login
      await act(async () => {
        screen.getByTestId('login-btn').click();

      // Should remain unauthenticated
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('null');



  describe('Logout Method', () => {
    it('should clear authentication state and redirect to login', async () => {
      const mockUserData = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      // Start with authenticated state
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue(mockUserData);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for initial authentication
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');

      // Trigger logout
      await act(async () => {
        screen.getByTestId('logout-btn').click();

      // Should clear authentication state
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('user-email')).toHaveTextContent('null');
      expect(screen.getByTestId('user-id')).toHaveTextContent('null');
      expect(screen.getByTestId('user-roles')).toHaveTextContent('null');

      // Should call session logout
      expect(mockLogout).toHaveBeenCalledTimes(1);

      // Should redirect to login
      expect(mockLocation.href).toBe('/login');

    it('should handle logout errors gracefully', async () => {
      mockLogout.mockRejectedValueOnce(new Error('Logout failed'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger logout
      await act(async () => {
        screen.getByTestId('logout-btn').click();

      // Should still clear state and redirect
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      expect(mockLocation.href).toBe('/login');


  describe('CheckAuth Method', () => {
    it('should return true and set state for valid session', async () => {
      const mockUserData = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue(mockUserData);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger checkAuth
      await act(async () => {
        screen.getByTestId('check-auth-btn').click();

      // Should be authenticated
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');


    it('should return false and clear state for invalid session', async () => {
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(false);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger checkAuth
      await act(async () => {
        screen.getByTestId('check-auth-btn').click();

      // Should not be authenticated
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('null');


    it('should return false when no session cookie exists', async () => {
      mockHasSessionCookie.mockReturnValue(false);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger checkAuth
      await act(async () => {
        screen.getByTestId('check-auth-btn').click();

      // Should not be authenticated
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('null');


    it('should handle validation errors gracefully', async () => {
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockRejectedValue(new Error('Network error'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger checkAuth
      await act(async () => {
        screen.getByTestId('check-auth-btn').click();

      // Should not be authenticated on error
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('null');


    it('should clear state if user data is missing after validation', async () => {
      mockHasSessionCookie.mockReturnValue(true);
      mockValidateSession.mockResolvedValue(true);
      mockGetCurrentUser.mockReturnValue(null); // No user data

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Trigger checkAuth
      await act(async () => {
        screen.getByTestId('check-auth-btn').click();

      // Should not be authenticated without user data
      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('null');



  describe('Single Source of Truth', () => {
    it('should maintain consistent state across all operations', async () => {
      const mockUserData = {
        userId: 'user123',
        email: 'test@example.com',
        roles: ['user'],
        tenantId: 'tenant123',
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Initially not authenticated
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');

      // Login
      mockLogin.mockResolvedValueOnce(undefined);
      mockGetCurrentUser.mockReturnValue(mockUserData);

      await act(async () => {
        screen.getByTestId('login-btn').click();

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');

      // Logout
      await act(async () => {
        screen.getByTestId('logout-btn').click();

      // Should be consistently unauthenticated
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('user-email')).toHaveTextContent('null');
      expect(screen.getByTestId('user-id')).toHaveTextContent('null');
      expect(screen.getByTestId('user-roles')).toHaveTextContent('null');


  describe('Error Boundaries', () => {
    it('should throw error when useAuth is used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleSpy.mockRestore();


