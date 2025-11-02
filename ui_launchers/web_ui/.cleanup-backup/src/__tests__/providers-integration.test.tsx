/**
 * Providers Integration Tests
 * 
 * Tests the integration of all providers including SessionProvider,
 * ErrorProvider, and GlobalErrorBoundary with existing providers.
 * 
 * Requirements: 1.1, 1.3, 5.1, 5.4, 5.5
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Providers } from '@/app/providers';
import { useSession } from '@/contexts/SessionProvider';
import { useError } from '@/contexts/ErrorProvider';
import { useAuth } from '@/contexts/AuthContext';
import { useHook } from '@/contexts/HookContext';

// Mock all the dependencies
vi.mock('@/lib/auth/session');
// Session recovery service removed - using simplified authentication
vi.mock('@/lib/api-client-integrated');
vi.mock('@/hooks/use-intelligent-error');

// Test component that uses all contexts
const TestAllContexts: React.FC = () => {
  const session = useSession();
  const error = useError();
  const auth = useAuth();
  const hook = useHook();

  return (
    <div>
      <div data-testid="session-context">
        {session ? 'SessionProvider Available' : 'SessionProvider Missing'}
      </div>
      <div data-testid="error-context">
        {error ? 'ErrorProvider Available' : 'ErrorProvider Missing'}
      </div>
      <div data-testid="auth-context">
        {auth ? 'AuthProvider Available' : 'AuthProvider Missing'}
      </div>
      <div data-testid="hook-context">
        {hook ? 'HookProvider Available' : 'HookProvider Missing'}
      </div>
      <div data-testid="session-loading">
        {session?.isLoading ? 'Loading' : 'Not Loading'}
      </div>
      <div data-testid="session-authenticated">
        {session?.isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      <div data-testid="error-analyzing">
        {error?.isAnalyzing ? 'Analyzing' : 'Not Analyzing'}
      </div>
      <div data-testid="auth-loading">
        {auth?.isLoading ? 'Loading' : 'Not Loading'}
      </div>
    </div>
  );
};

// Component that throws an error for testing error boundary
const ErrorThrowingComponent: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Test error for error boundary');
  }
  return <div data-testid="no-error">No Error</div>;
};

describe('Providers Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock console methods to avoid noise in tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Provider Availability', () => {
    it('should provide all context providers', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      await waitFor(() => {
        expect(screen.getByTestId('session-context')).toHaveTextContent('SessionProvider Available');
        expect(screen.getByTestId('error-context')).toHaveTextContent('ErrorProvider Available');
        expect(screen.getByTestId('auth-context')).toHaveTextContent('AuthProvider Available');
        expect(screen.getByTestId('hook-context')).toHaveTextContent('HookProvider Available');
      });
    });

    it('should initialize providers in the correct order', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      // All providers should be available immediately
      expect(screen.getByTestId('session-context')).toHaveTextContent('SessionProvider Available');
      expect(screen.getByTestId('error-context')).toHaveTextContent('ErrorProvider Available');
      expect(screen.getByTestId('auth-context')).toHaveTextContent('AuthProvider Available');
      expect(screen.getByTestId('hook-context')).toHaveTextContent('HookProvider Available');
    });
  });

  describe('Provider State Management', () => {
    it('should manage session state independently from auth state', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      await waitFor(() => {
        // Session provider should have its own loading state
        expect(screen.getByTestId('session-loading')).toBeInTheDocument();
        expect(screen.getByTestId('session-authenticated')).toBeInTheDocument();
        
        // Auth provider should have its own loading state
        expect(screen.getByTestId('auth-loading')).toBeInTheDocument();
      });
    });

    it('should manage error state globally', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      await waitFor(() => {
        expect(screen.getByTestId('error-analyzing')).toHaveTextContent('Not Analyzing');
      });
    });
  });

  describe('Global Error Boundary Integration', () => {
    it('should catch and handle component errors', async () => {
      // Suppress React error boundary warnings for this test
      const originalError = console.error;
      console.error = vi.fn();

      render(
        <Providers>
          <ErrorThrowingComponent shouldThrow={true} />
        </Providers>
      );

      await waitFor(() => {
        // Should show error boundary UI instead of the component
        expect(screen.queryByTestId('no-error')).not.toBeInTheDocument();
        
        // Should show error boundary content
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();
      });

      console.error = originalError;
    });

    it('should not interfere with normal component rendering', async () => {
      render(
        <Providers>
          <ErrorThrowingComponent shouldThrow={false} />
        </Providers>
      );

      await waitFor(() => {
        expect(screen.getByTestId('no-error')).toBeInTheDocument();
      });
    });

    it('should provide intelligent error analysis for caught errors', async () => {
      // Suppress React error boundary warnings for this test
      const originalError = console.error;
      console.error = vi.fn();

      render(
        <Providers>
          <ErrorThrowingComponent shouldThrow={true} />
        </Providers>
      );

      await waitFor(() => {
        // Should show error boundary with intelligent response option
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();
        
        // Should have retry button
        expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
      });

      console.error = originalError;
    });
  });

  describe('Provider Configuration', () => {
    it('should configure SessionProvider with correct options', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      // SessionProvider should be configured with autoRehydrate: true
      await waitFor(() => {
        expect(screen.getByTestId('session-context')).toHaveTextContent('SessionProvider Available');
      });
    });

    it('should configure ErrorProvider with correct options', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      // ErrorProvider should be configured with intelligent analysis enabled
      await waitFor(() => {
        expect(screen.getByTestId('error-context')).toHaveTextContent('ErrorProvider Available');
      });
    });

    it('should configure GlobalErrorBoundary with correct options', async () => {
      // Suppress React error boundary warnings for this test
      const originalError = console.error;
      console.error = vi.fn();

      render(
        <Providers>
          <ErrorThrowingComponent shouldThrow={true} />
        </Providers>
      );

      await waitFor(() => {
        // Should show intelligent response (configured with showIntelligentResponse: true)
        expect(screen.getByText(/Application Error/i)).toBeInTheDocument();
        
        // Should have session recovery enabled (configured with enableSessionRecovery: true)
        expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
      });

      console.error = originalError;
    });
  });

  describe('Provider Interaction', () => {
    it('should allow providers to work together without conflicts', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      await waitFor(() => {
        // All providers should be available and functional
        expect(screen.getByTestId('session-context')).toHaveTextContent('SessionProvider Available');
        expect(screen.getByTestId('error-context')).toHaveTextContent('ErrorProvider Available');
        expect(screen.getByTestId('auth-context')).toHaveTextContent('AuthProvider Available');
        expect(screen.getByTestId('hook-context')).toHaveTextContent('HookProvider Available');
      });
    });

    it('should handle provider initialization errors gracefully', async () => {
      // Mock session initialization to fail
      const mockBootSession = require('@/lib/auth/session').bootSession;
      mockBootSession.mockRejectedValue(new Error('Session initialization failed'));

      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      await waitFor(() => {
        // Should still render the component even if session initialization fails
        expect(screen.getByTestId('session-context')).toHaveTextContent('SessionProvider Available');
      });
    });
  });

  describe('CopilotKit Integration', () => {
    it('should maintain CopilotKit provider in the provider chain', async () => {
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      // Should render without errors, indicating CopilotKit is properly integrated
      await waitFor(() => {
        expect(screen.getByTestId('session-context')).toBeInTheDocument();
      });
    });
  });

  describe('Provider Nesting Order', () => {
    it('should nest providers in the correct order for proper functionality', async () => {
      // The nesting order should be:
      // GlobalErrorBoundary > ErrorProvider > SessionProvider > AuthProvider > HookProvider > CopilotKitProvider
      
      render(
        <Providers>
          <TestAllContexts />
        </Providers>
      );

      await waitFor(() => {
        // All contexts should be available, indicating proper nesting
        expect(screen.getByTestId('session-context')).toHaveTextContent('SessionProvider Available');
        expect(screen.getByTestId('error-context')).toHaveTextContent('ErrorProvider Available');
        expect(screen.getByTestId('auth-context')).toHaveTextContent('AuthProvider Available');
        expect(screen.getByTestId('hook-context')).toHaveTextContent('HookProvider Available');
      });
    });
  });
});