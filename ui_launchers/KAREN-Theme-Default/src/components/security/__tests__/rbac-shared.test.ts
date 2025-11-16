import { describe, expect, it } from 'vitest';

import {
  getHighestRole,
  getRolePermissions,
  isValidRole,
  ROLE_PERMISSIONS,
  roleHasPermission,
} from '../rbac-shared';

describe('rbac-shared permission configuration', () => {
  it('exposes permissions for every configured role via ROLE_PERMISSIONS proxy', () => {
    const routingOperatorPerms = ROLE_PERMISSIONS['routing_operator'] ?? [];
    expect(routingOperatorPerms).toContain('routing:select');
    expect(routingOperatorPerms).toContain('routing:dry_run');
  });

  it('resolves inherited permissions for admin roles', () => {
    const adminPermissions = getRolePermissions('admin');
    expect(adminPermissions).toContain('admin:write');
    expect(adminPermissions).toContain('routing:select');
  });

  it('ensures super admins cover every subordinate role without leaking elevated-only scopes', () => {
    const superAdminPermissions = getRolePermissions('super_admin');
    const adminPermissions = getRolePermissions('admin');
    const userPermissions = getRolePermissions('user');

    expect(superAdminPermissions).toContain('security:evil_mode');
    expect(adminPermissions).not.toContain('security:evil_mode');

    for (const permission of adminPermissions) {
      expect(superAdminPermissions).toContain(permission);
    }

    for (const permission of userPermissions) {
      expect(superAdminPermissions).toContain(permission);
    }
  });

  it('computes the highest ranked role using ROLE_HIERARCHY ordering', () => {
    expect(getHighestRole(['user', 'trainer'])).toBe('trainer');
    expect(getHighestRole(['routing_auditor', 'readonly'])).toBe('routing_auditor');
  });

  it('validates known roles from permissions config', () => {
    expect(isValidRole('routing_admin')).toBe(true);
    expect(isValidRole('unknown_role')).toBe(false);
  });

  it('checks permissions using the roleHasPermission helper', () => {
    expect(roleHasPermission('readonly', 'model:read')).toBe(true);
    expect(roleHasPermission('readonly', 'model:write')).toBe(false);
  });
});
