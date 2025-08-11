import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { AuthenticatedHeader } from '../AuthenticatedHeader';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { user_id: 'user123', roles: ['user'] },
    logout: vi.fn(),
  }),
}));

test('renders without crashing when user email is undefined', async () => {
  render(<AuthenticatedHeader />);
  expect(screen.getByText('U')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('user123')).toBeInTheDocument();
});
