/**
 * Integration tests for ProtectedRoute component
 * Tests the protected route functionality and LoginForm integration
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ProtectedRoute } from '../ProtectedRoute';
import { AuthProvider } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';

// Mock the authService
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

// Mock the LoginForm component
vi.mock('../LoginForm', () => ({
  LoginForm: () => <div data-testid="login-form">Login Form</div>,
}));

// Session rehydration service removed - using simplified authentication
vi.mock('@/lib/auth/session', () => ({
  isAuthenticated: vi.fn(),
  validateSession: vi.fn().mockResolvedValue(true),
}));

const mockAuthService = authService as any;

const renderWithAuthProvider = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

const ProtectedContent = () => (
  <div data-testid="protected-content">Protected Content</div>
);

describe('ProtectedRoute Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  describe('Authentication State Handling', () => {
    it('should show loading state while checking authentication', async () => {
      // Mock getCurrentUser to never resolve to simulate loading
      let resolveAuth: (value: any) => void;
      const authPromise = new Promise((resolve) => {
        resolveAuth = resolve;

      mockAuthService.getCurrentUser.mockReturnValue(authPromise);

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Should show loading state
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument();

      // Resolve authentication check
      resolveAuth!({
        user_id: 'test-user',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {},

      // Wait for authentication to complete
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();


    it('should show LoginForm when user is not authenticated', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Wait for authentication check to complete
      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();

    it('should show protected content when user is authenticated', async () => {
      const mockUser = {
        user_id: 'test-user',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'llama-cpp',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: { email: true, push: false },
          ui: { theme: 'light', language: 'en', avatarUrl: '' },
        },
      };

      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Wait for authentication check to complete
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument();
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();

    it('should show custom fallback when provided and user is not authenticated', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

      const CustomFallback = () => (
        <div data-testid="custom-fallback">Custom Login Component</div>
      );

      renderWithAuthProvider(
        <ProtectedRoute fallback={<CustomFallback />}>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Wait for authentication check to complete
      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();


  describe('Authentication State Transitions', () => {
    it('should transition from loading to login form when authentication fails', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Not authenticated'));

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Initially shows loading
      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      // Wait for transition to login form
      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();

      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    it('should transition from loading to protected content when authentication succeeds', async () => {
      const mockUser = {
        user_id: 'test-user',
        email: 'test@example.com',
        roles: ['user'],
        tenant_id: 'test-tenant',
        two_factor_enabled: false,
        preferences: {
          personalityTone: 'friendly',
          personalityVerbosity: 'balanced',
          memoryDepth: 'medium',
          customPersonaInstructions: '',
          preferredLLMProvider: 'llama-cpp',
          preferredModel: 'llama3.2:latest',
          temperature: 0.7,
          maxTokens: 1000,
          notifications: { email: true, push: false },
          ui: { theme: 'light', language: 'en', avatarUrl: '' },
        },
      };

      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Initially shows loading
      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      // Wait for transition to protected content
      await waitFor(() => {
        expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument();


  describe('Error Handling', () => {
    it('should handle authentication service errors gracefully', async () => {
      // Mock a network error
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Network error'));

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Should fall back to login form on any authentication error
      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

    it('should handle malformed user data gracefully', async () => {
      // Mock invalid user data by rejecting with an error
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Invalid user data'));

      renderWithAuthProvider(
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      );

      // Should treat invalid user data as unauthenticated
      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument();

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();


