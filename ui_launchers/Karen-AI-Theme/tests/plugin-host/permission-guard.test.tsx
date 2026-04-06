import { vi, describe, it, expect } from 'vitest';
import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

// Ensure no stray characters
vi.mock('@/lib/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'test-user', roles: ['user', 'admin'] },
    loading: false,
    error: null
  })
}));

// We import the component AFTER the mock
import { PermissionGuard } from '../../src/plugin_host/permission-guard';

describe('Permission Guard', () => {
  it('should render children when user has required role', () => {
    const { container } = render(
      <PermissionGuard pluginId="test-plugin" requiredRoles={['user']}>
        <div>Test Content</div>
      </PermissionGuard>
    );
    expect(container.querySelector('div')).toHaveTextContent('Test Content');
  });

  it('should not render children when user lacks required role', () => {
    const { container } = render(
      <PermissionGuard pluginId="test-plugin" requiredRoles={['developer']}>
        <div>Test Content</div>
      </PermissionGuard>
    );
    expect(container.querySelector('div')).toBeNull();
  });
});