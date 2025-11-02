"use client";

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useFeature } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';

export type UserRole = 'admin' | 'user' | 'guest' | 'moderator' | 'developer';
export type Permission = 
  | 'chat.send' 
  | 'chat.code_assistance' 
  | 'chat.explanations'
  | 'chat.documentation'
  | 'chat.analysis'
  | 'voice.input'
  | 'voice.output'
  | 'attachments.upload'
  | 'attachments.download'
  | 'admin.settings'
  | 'admin.users'
  | 'developer.debug'
  | 'moderator.content';

interface RBACGuardProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  requiredPermission?: Permission;
  featureFlag?: string;
  fallback?: React.ReactNode;
  onAccessDenied?: (reason: string) => void;
  className?: string;
}

// Role hierarchy - higher roles inherit permissions from lower roles
const ROLE_HIERARCHY: Record<UserRole, number> = {
  guest: 0,
  user: 1,
  moderator: 2,
  developer: 3,
  admin: 4
};

// Permission mappings for each role
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  guest: [
    'chat.send'
  ],
  user: [
    'chat.send',
    'chat.code_assistance',
    'chat.explanations',
    'chat.documentation',
    'chat.analysis',
    'voice.input',
    'voice.output',
    'attachments.upload',
    'attachments.download'
  ],
  moderator: [
    'chat.send',
    'chat.code_assistance',
    'chat.explanations',
    'chat.documentation',
    'chat.analysis',
    'voice.input',
    'voice.output',
    'attachments.upload',
    'attachments.download',
    'moderator.content'
  ],
  developer: [
    'chat.send',
    'chat.code_assistance',
    'chat.explanations',
    'chat.documentation',
    'chat.analysis',
    'voice.input',
    'voice.output',
    'attachments.upload',
    'attachments.download',
    'developer.debug'
  ],
  admin: [
    'chat.send',
    'chat.code_assistance',
    'chat.explanations',
    'chat.documentation',
    'chat.analysis',
    'voice.input',
    'voice.output',
    'attachments.upload',
    'attachments.download',
    'moderator.content',
    'developer.debug',
    'admin.settings',
    'admin.users'
  ]
};

export const RBACGuard: React.FC<RBACGuardProps> = ({
  children,
  requiredRole,
  requiredPermission,
  featureFlag,
  fallback = null,
  onAccessDenied,
  className
}) => {
  const { user, isAuthenticated } = useAuth();
  const { track } = useTelemetry();
  
  // Check feature flag first
  const isFeatureEnabled = useFeature(featureFlag);
  if (featureFlag && !isFeatureEnabled) {
    track('rbac_access_denied', { 
      reason: 'feature_disabled', 
      featureFlag,
      userId: user?.userId 

    onAccessDenied?.('Feature is currently disabled');
    return <>{fallback}</>;
  }

  // Check authentication
  if (!isAuthenticated || !user) {
    track('rbac_access_denied', { 
      reason: 'not_authenticated',
      requiredRole,
      requiredPermission,
      userId: null

    onAccessDenied?.('Authentication required');
    return <>{fallback}</>;
  }

  const userRole = (user.roles?.[0] || 'guest') as UserRole;
  const userRoleLevel = ROLE_HIERARCHY[userRole] || 0;

  // Check role requirement
  if (requiredRole) {
    const requiredRoleLevel = ROLE_HIERARCHY[requiredRole] || 0;
    
    if (userRoleLevel < requiredRoleLevel) {
      track('rbac_access_denied', { 
        reason: 'insufficient_role',
        userRole,
        requiredRole,
        userId: user.userId

      onAccessDenied?.(`Role '${requiredRole}' required, but user has '${userRole}'`);
      return <>{fallback}</>;
    }
  }

  // Check permission requirement
  if (requiredPermission) {
    const userPermissions = ROLE_PERMISSIONS[userRole] || [];
    
    if (!userPermissions.includes(requiredPermission)) {
      track('rbac_access_denied', { 
        reason: 'insufficient_permission',
        userRole,
        requiredPermission,
        userPermissions,
        userId: user.userId

      onAccessDenied?.(`Permission '${requiredPermission}' required`);
      return <>{fallback}</>;
    }
  }

  // Access granted
  track('rbac_access_granted', {
    userRole,
    requiredRole,
    requiredPermission,
    featureFlag,
    userId: user.userId

  return (
    <div className={className} data-rbac-protected="true">
      {children}
    </div>
  );
};

// Utility hook for checking permissions in components
export const usePermissions = () => {
  const { user, isAuthenticated } = useAuth();
  
  const hasRole = (role: UserRole): boolean => {
    if (!isAuthenticated || !user) return false;
    
    const userRole = (user.roles?.[0] || 'guest') as UserRole;
    const userRoleLevel = ROLE_HIERARCHY[userRole] || 0;
    const requiredRoleLevel = ROLE_HIERARCHY[role] || 0;
    
    return userRoleLevel >= requiredRoleLevel;
  };
  
  const hasPermission = (permission: Permission): boolean => {
    if (!isAuthenticated || !user) return false;
    
    const userRole = (user.roles?.[0] || 'guest') as UserRole;
    const userPermissions = ROLE_PERMISSIONS[userRole] || [];
    
    return userPermissions.includes(permission);
  };
  
  const canAccess = (options: {
    role?: UserRole;
    permission?: Permission;
    featureFlag?: string;
  }): boolean => {
    if (options.featureFlag && !useFeature(options.featureFlag)) {
      return false;
    }
    
    if (options.role && !hasRole(options.role)) {
      return false;
    }
    
    if (options.permission && !hasPermission(options.permission)) {
      return false;
    }
    
    return true;
  };
  
  return {
    hasRole,
    hasPermission,
    canAccess,
    userRole: (user?.roles?.[0] || 'guest') as UserRole,
    isAuthenticated
  };
};

export default RBACGuard;