"use client";

/**
 * PermissionGuard — renders children only when the current user has at least
 * one of the required roles.
 *
 * Rules:
 * - When `requiredRoles` is empty or absent, children are always rendered.
 * - When `requiredRoles` is non-empty, children are rendered iff the user's
 *   roles intersect with `requiredRoles`.
 * - Renders `null` when the user lacks all required roles.
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
 */

import React from 'react';
import { useAuth } from '@/lib/useAuth';

export interface PermissionGuardProps {
  /** Canonical plugin ID (used for debugging / aria labelling) */
  pluginId: string;
  /** Roles that are allowed to see the children. Empty = allow all. */
  requiredRoles?: string[];
  children: React.ReactNode;
}

/**
 * Renders `children` when the current user satisfies the role requirement.
 *
 * @example
 * <PermissionGuard pluginId="weather-query" requiredRoles={['admin', 'user']}>
 *   <WeatherPlugin />
 * </PermissionGuard>
 */
export function PermissionGuard({
  requiredRoles,
  children,
}: PermissionGuardProps): React.ReactElement | null {
  const { user } = useAuth();

  // No role restriction — always render
  if (!requiredRoles || requiredRoles.length === 0) {
    return <>{children}</>;
  }

  const userRoles: string[] = user?.roles ?? [];

  // Render children iff user has at least one matching role
  const hasAccess = userRoles.some((role) => requiredRoles.includes(role));

  if (!hasAccess) {
    // Silently hide — no error UI, just omit the entry
    return null;
  }

  return <>{children}</>;
}

export default PermissionGuard;
