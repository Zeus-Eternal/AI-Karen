import { describe, it, expect, vi } from 'vitest';
import { PermissionGuard } from '../../src/plugin_host/permission-guard';
import { render } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'test-user', roles: ['user', 'admin'] },
    loading: false,
    error: null
  })
}));

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

  it('should render children when no roles are required', () => {
    const { container } = render(
      <PermissionGuard pluginId="test-plugin">
        <div>Test Content</div>
      </PermissionGuard>
    );
    expect(container.querySelector('div')).toHaveTextContent('Test Content');
  });
});