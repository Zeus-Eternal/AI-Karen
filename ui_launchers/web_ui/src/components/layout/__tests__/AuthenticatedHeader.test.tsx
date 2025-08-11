import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { AuthenticatedHeader } from '../AuthenticatedHeader';

const mockUseAuth = vi.fn();
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

beforeEach(() => {
  mockUseAuth.mockReset();
});

test('renders user id and joined roles when roles array provided', async () => {
  mockUseAuth.mockReturnValue({
    user: { user_id: 'user123', roles: ['admin', 'user'] },
    logout: vi.fn(),
  });

  render(<AuthenticatedHeader />);
  expect(screen.getByText('U')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('user123')).toBeInTheDocument();
  expect(screen.getByText('admin, user')).toBeInTheDocument();
});

test('renders without crashing when user roles are undefined', async () => {
  mockUseAuth.mockReturnValue({
    user: { user_id: 'user123' },
    logout: vi.fn(),
  });

  render(<AuthenticatedHeader />);
  expect(screen.getByText('U')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('user123')).toBeInTheDocument();
});

test('renders role string when user roles is a string', async () => {
  mockUseAuth.mockReturnValue({
    user: { user_id: 'user123', roles: 'admin' },
    logout: vi.fn(),
  });

  render(<AuthenticatedHeader />);
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('admin')).toBeInTheDocument();
});

