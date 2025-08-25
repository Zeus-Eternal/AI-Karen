import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('@/components/auth/LoginForm', () => ({
  LoginForm: () => <div data-testid="login-form">Login Form</div>,
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const rehydrateMock = vi.fn();
vi.mock('@/lib/auth/session-rehydration.service', () => ({
  SessionRehydrationService: vi.fn(() => ({ rehydrate: rehydrateMock })),
}));

import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    rehydrateMock.mockReset();
  });

  it('renders children when authenticated', async () => {
    useAuth.mockReturnValue({ isAuthenticated: true, isLoading: false });
    rehydrateMock.mockResolvedValue(undefined);
    render(
      <ProtectedRoute>
        <div data-testid="child">Child</div>
      </ProtectedRoute>
    );
    await waitFor(() => expect(screen.getByTestId('child')).toBeInTheDocument());
  });

  it('shows loader while rehydrating', () => {
    useAuth.mockReturnValue({ isAuthenticated: false, isLoading: false });
    rehydrateMock.mockImplementation(() => new Promise(() => {}));
    render(
      <ProtectedRoute>
        <div>Child</div>
      </ProtectedRoute>
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('allows retry on rehydration error', async () => {
    useAuth.mockReturnValue({ isAuthenticated: false, isLoading: false });
    rehydrateMock.mockRejectedValueOnce(new Error('fail')).mockResolvedValueOnce(undefined);
    render(
      <ProtectedRoute>
        <div data-testid="child">Child</div>
      </ProtectedRoute>
    );
    await waitFor(() => screen.getByText('fail'));
    fireEvent.click(screen.getByTestId('retry-button'));
    await waitFor(() => expect(rehydrateMock).toHaveBeenCalledTimes(2));
  });
});
