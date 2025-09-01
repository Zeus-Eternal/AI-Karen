/**
 * Authentication Health Check
 * Diagnoses and fixes common auth issues causing 401 errors
 */

import { bootSession, clearSession, isAuthenticated, getSession } from './auth/session';
import { getAuthDebugInfo, logAuthStatus } from './auth-debug';

export interface AuthHealthResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  issues: string[];
  fixes: string[];
  canRetry: boolean;
}

export async function checkAuthHealth(): Promise<AuthHealthResult> {
  const result: AuthHealthResult = {
    status: 'healthy',
    issues: [],
    fixes: [],
    canRetry: false
  };

  const debugInfo = getAuthDebugInfo();
  
  // Check 1: No session at all
  if (!debugInfo.hasSession) {
    result.issues.push('No active session found');
    result.fixes.push('Attempting to restore session from cookies');
    result.canRetry = true;
    
    try {
      await bootSession();
      const newDebugInfo = getAuthDebugInfo();
      if (newDebugInfo.hasSession) {
        result.fixes.push('✅ Session restored successfully');
      } else {
        result.fixes.push('❌ Could not restore session - login required');
        result.status = 'unhealthy';
      }
    } catch (error) {
      result.fixes.push(`❌ Session restore failed: ${error}`);
      result.status = 'unhealthy';
    }
  }
  
  // Check 2: Session exists but is invalid/expired
  else if (!debugInfo.isValid) {
    result.issues.push('Session exists but is invalid or expired');
    result.fixes.push('Clearing invalid session');
    clearSession();
    result.canRetry = true;
    result.status = 'degraded';
  }
  
  // Check 3: Session expires soon
  else if (debugInfo.timeUntilExpiry && debugInfo.timeUntilExpiry < 300000) { // 5 minutes
    result.issues.push(`Session expires soon (${Math.round(debugInfo.timeUntilExpiry / 1000)}s)`);
    result.fixes.push('Consider refreshing token proactively');
    result.status = 'degraded';
  }
  
  // Check 4: Token storage inconsistency
  if (debugInfo.tokens.localStorage !== debugInfo.tokens.sessionStorage) {
    result.issues.push('Token storage inconsistency between localStorage and sessionStorage');
    result.fixes.push('Synchronizing token storage');
    result.status = 'degraded';
  }
  
  // Check 5: No authentication tokens but has cookies
  if (!debugInfo.tokens.localStorage && !debugInfo.tokens.sessionStorage && debugInfo.cookies.length > 0) {
    result.issues.push('Has cookies but no stored tokens - possible HttpOnly session');
    result.fixes.push('This is normal for HttpOnly cookie authentication');
  }
  
  return result;
}

export async function fixAuthIssues(): Promise<boolean> {
  console.log('🔧 Running authentication health check and fixes...');
  
  const healthResult = await checkAuthHealth();
  
  console.group('🏥 Auth Health Report');
  console.log('Status:', healthResult.status);
  console.log('Issues:', healthResult.issues);
  console.log('Fixes Applied:', healthResult.fixes);
  console.groupEnd();
  
  if (healthResult.status === 'unhealthy') {
    console.warn('❌ Authentication is unhealthy - user may need to log in again');
    return false;
  }
  
  if (healthResult.status === 'degraded') {
    console.warn('⚠️ Authentication is degraded but functional');
    return true;
  }
  
  console.log('✅ Authentication is healthy');
  return true;
}

// Auto-run health check on import in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  // Run health check after a short delay to avoid blocking initial load
  setTimeout(() => {
    fixAuthIssues().catch(console.error);
  }, 1000);
}