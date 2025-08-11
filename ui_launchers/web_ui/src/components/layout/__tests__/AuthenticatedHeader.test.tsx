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

test('renders without crashing when user email is undefined', async () => {
  mockUseAuth.mockReturnValue({
    user: { user_id: 'user123', roles: ['user'] },
    logout: vi.fn(),
  });

  render(<AuthenticatedHeader />);
  expect(screen.getByText('U')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('user123')).toBeInTheDocument();
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

