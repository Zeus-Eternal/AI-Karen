import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, test } from 'vitest';
import '@testing-library/jest-dom/vitest';
import Dashboard from '../Dashboard';

// Mock authentication context
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      user_id: 'user1',
      roles: ['user'],
      tenant_id: 'tenant1',
      two_factor_enabled: false,
      preferences: {} as any,
      email: undefined
    }
  })
}));

// Mock dashboard dependencies
vi.mock('../monitoring/health-dashboard', () => ({
  HealthDashboard: () => <div />
}));

vi.mock('../analytics/UsageAnalyticsCharts', () => ({
  __esModule: true,
  default: () => <div />
}));

vi.mock('../analytics/AuditLogTable', () => ({
  __esModule: true,
  default: () => <div />
}));

test('renders fallback when user email is undefined', () => {
  render(<Dashboard />);
  expect(screen.getByText('Welcome, User')).toBeInTheDocument();
});
