"use client";

import React, { useEffect, useState } from 'react';
import { useChatAuth } from '@/contexts/ChatAuthContext';
import { useSecurity } from '@/hooks/useSecurity';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Lock, Shield, AlertTriangle, UserX } from 'lucide-react';

// Types for AuthGuard
export interface AuthGuardProps {
  children: React.ReactNode;
  requiredPermission?: string;
  requiredPermissions?: string[];
  requireAll?: boolean; // If true, user must have ALL permissions; if false, ANY permission is sufficient
  securityLevel?: 'low' | 'medium' | 'high' | 'strict';
  fallback?: React.ReactNode;
  redirectTo?: string;
  showLoginPrompt?: boolean;
  showPermissionDenied?: boolean;
  customMessage?: string;
  onAccessDenied?: () => void;
  className?: string;
}

export interface AccessDeniedProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  showLoginButton?: boolean;
  showRetryButton?: boolean;
  onRetry?: () => void;
  onLogin?: () => void;
  className?: string;
}

// Access denied component
function AccessDenied({
  title = "Access Denied",
  description = "You don't have permission to access this resource.",
  icon = <Lock className="h-6 w-6" />,
  showLoginButton = true,
  showRetryButton = false,
  onRetry,
  onLogin,
  className = ""
}: AccessDeniedProps) {
  return (
    <Card className={`w-full max-w-md mx-auto ${className}`}>
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-600">
          {icon}
        </div>
        <CardTitle className="text-red-600">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {showLoginButton && (
          <Button onClick={onLogin} className="w-full">
            <UserX className="mr-2 h-4 w-4" />
            Sign In
          </Button>
        )}
        {showRetryButton && onRetry && (
          <Button variant="outline" onClick={onRetry} className="w-full">
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// Security level warning component
function SecurityLevelWarning({
  currentLevel,
  requiredLevel,
  onUpgrade
}: {
  currentLevel: 'low' | 'medium' | 'high' | 'strict';
  requiredLevel: 'low' | 'medium' | 'high' | 'strict';
  onUpgrade?: () => void;
}) {
  const levelOrder: Record<string, number> = { low: 1, medium: 2, high: 3, strict: 4 };
  const isUpgradeRequired = (levelOrder[requiredLevel] || 0) > (levelOrder[currentLevel] || 0);
  
  if (!isUpgradeRequired) return null;
  
  return (
    <Alert className="mb-4">
      <Shield className="h-4 w-4" />
      <AlertTitle>Security Level Required</AlertTitle>
      <AlertDescription>
        This resource requires {requiredLevel} security level. Your current level is {currentLevel}.
        {onUpgrade && (
          <Button
            variant="ghost"
            onClick={onUpgrade}
            className="mt-2 p-0 h-auto font-normal"
          >
            Upgrade Security Level
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

// Session expired component
function SessionExpired({ onRefresh }: { onRefresh?: () => void }) {
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-yellow-100 text-yellow-600">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <CardTitle className="text-yellow-600">Session Expired</CardTitle>
        <CardDescription>
          Your session has expired due to inactivity. Please sign in again to continue.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button onClick={onRefresh} className="w-full">
          Refresh Session
        </Button>
      </CardContent>
    </Card>
  );
}

// Main AuthGuard component
export function AuthGuard({
  children,
  requiredPermission,
  requiredPermissions = [],
  requireAll = false,
  securityLevel,
  fallback,
  redirectTo,
  showLoginPrompt = true,
  showPermissionDenied = true,
  customMessage,
  onAccessDenied,
  className = ""
}: AuthGuardProps) {
  const chatAuth = useChatAuth();
  const security = useSecurity();
  
  const { 
    checkChatPermission,
    login,
    refreshSession
  } = chatAuth;
  
  const {
    securityLevel: currentSecurityLevel,
    setSecurityLevel,
    logSecurityEvent
  } = security;
  
  const {
    chatAuthState
  } = chatAuth;
  
  const {
    isAuthenticated,
    hasChatAccess,
    isLoading,
    error
  } = chatAuthState;

  const [isChecking, setIsChecking] = useState(true);
  const [accessState, setAccessState] = useState<'loading' | 'granted' | 'denied' | 'expired' | 'upgrade'>('loading');

  // Check permissions
  const hasPermission = requiredPermission 
    ? checkChatPermission(requiredPermission)
    : requiredPermissions.length > 0
      ? requireAll 
        ? requiredPermissions.every(perm => checkChatPermission(perm))
        : requiredPermissions.some(perm => checkChatPermission(perm))
      : true;

  // Check security level
  const hasSecurityLevel = securityLevel
    ? (() => {
        const levelOrder: Record<string, number> = { low: 1, medium: 2, high: 3, strict: 4 };
        return (levelOrder[currentSecurityLevel.level] || 0) >= (levelOrder[securityLevel] || 0);
      })()
    : true;

  // Check rate limiting
  const rateLimitOk = true;

  // Perform access checks
  useEffect(() => {
    const performAccessCheck = async () => {
      setIsChecking(true);
      
      // Simulate async check for demonstration
      await new Promise(resolve => setTimeout(resolve, 100));
      
      if (!isAuthenticated) {
        setAccessState('denied');
      } else if (chatAuthState.lastActivity &&
                (new Date().getTime() - chatAuthState.lastActivity.getTime() > 30 * 60 * 1000)) {
        setAccessState('expired');
      } else if (!hasChatAccess) {
        setAccessState('denied');
      } else if (!hasPermission) {
        setAccessState('denied');
        logSecurityEvent({
          type: 'security_violation',
          severity: 'medium',
          message: 'Access denied due to insufficient permissions',
          details: {
            requiredPermission,
            requiredPermissions,
            requireAll
          }
        });
      } else if (!hasSecurityLevel) {
        setAccessState('upgrade');
      } else if (!rateLimitOk) {
        setAccessState('denied');
        logSecurityEvent({
          type: 'security_violation',
          severity: 'medium',
          message: 'Rate limit exceeded for access check',
        });
      } else {
        setAccessState('granted');
      }
      
      setIsChecking(false);
    };
    
    performAccessCheck();
  }, [
    isAuthenticated, 
    hasChatAccess, 
    hasPermission, 
    hasSecurityLevel, 
    rateLimitOk,
    chatAuthState.lastActivity,
    requiredPermission,
    requiredPermissions,
    requireAll,
    securityLevel,
    currentSecurityLevel.level
  ]);

  // Handle access denied callback
  useEffect(() => {
    if (accessState === 'denied' && onAccessDenied) {
      onAccessDenied();
    }
  }, [accessState, onAccessDenied]);

  // Handle redirect
  useEffect(() => {
    if (accessState === 'denied' && redirectTo) {
      window.location.href = redirectTo;
    }
  }, [accessState, redirectTo]);

  // Show loading state
  if (isLoading || isChecking) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
          <span className="text-sm text-muted-foreground">Verifying access...</span>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Authentication Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Show custom fallback if provided
  if (accessState !== 'granted' && fallback) {
    return <div className={className}>{fallback}</div>;
  }

  // Show appropriate state based on access
  switch (accessState) {
    case 'granted':
      return <div className={className}>{children}</div>;
      
    case 'expired':
      return (
        <div className={`flex items-center justify-center p-8 ${className}`}>
          <SessionExpired onRefresh={refreshSession} />
        </div>
      );
      
    case 'upgrade':
      if (securityLevel) {
        return (
          <div className={`p-4 ${className}`}>
            <SecurityLevelWarning
              currentLevel={currentSecurityLevel.level}
              requiredLevel={securityLevel}
              onUpgrade={() => setSecurityLevel({ level: securityLevel, score: 0 })}
            />
            {showPermissionDenied && (
              <AccessDenied
                title="Security Level Required"
                description={`This resource requires ${securityLevel} security level.`}
                icon={<Shield className="h-6 w-6" />}
                showLoginButton={false}
              />
            )}
          </div>
        );
      }
      return null;
      
    case 'denied':
    default:
      if (!showPermissionDenied) {
        return null;
      }
      
      return (
        <div className={`flex items-center justify-center p-8 ${className}`}>
          <AccessDenied
            title={customMessage || "Access Denied"}
            description={
              customMessage || 
              (requiredPermission 
                ? `You need "${requiredPermission}" permission to access this resource.`
                : requiredPermissions.length > 0
                  ? `You need ${requireAll ? 'all' : 'one of'} the following permissions: ${requiredPermissions.join(', ')}`
                  : "You don't have permission to access this resource.")
            }
            showLoginButton={showLoginPrompt && !isAuthenticated}
            onLogin={() => login({ username: '', password: '' })}
          />
        </div>
      );
  }
}

// Higher-order component for wrapping components with AuthGuard
export function withAuthGuard<P extends object>(
  Component: React.ComponentType<P>,
  authGuardProps: Omit<AuthGuardProps, 'children'>
) {
  return function AuthGuardedComponent(props: P) {
    return (
      <AuthGuard {...authGuardProps}>
        <Component {...props} />
      </AuthGuard>
    );
  };
}

// Convenience components for common auth scenarios
export function AdminOnly({ children, ...props }: Omit<AuthGuardProps, 'requiredPermission'>) {
  return (
    <AuthGuard requiredPermission="chat:admin" {...props}>
      {children}
    </AuthGuard>
  );
}

export function ModeratorOnly({ children, ...props }: Omit<AuthGuardProps, 'requiredPermission'>) {
  return (
    <AuthGuard 
      requiredPermissions={['chat:moderate', 'chat:admin']} 
      requireAll={false}
      {...props}
    >
      {children}
    </AuthGuard>
  );
}

export function HighSecurityOnly({ children, ...props }: Omit<AuthGuardProps, 'securityLevel'>) {
  return (
    <AuthGuard securityLevel="high" {...props}>
      {children}
    </AuthGuard>
  );
}

export function StrictSecurityOnly({ children, ...props }: Omit<AuthGuardProps, 'securityLevel'>) {
  return (
    <AuthGuard securityLevel="strict" {...props}>
      {children}
    </AuthGuard>
  );
}

export default AuthGuard;