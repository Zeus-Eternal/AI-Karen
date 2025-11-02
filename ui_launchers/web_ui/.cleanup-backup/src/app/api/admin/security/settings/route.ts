import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';

/**
 * GET /api/admin/security/settings
 * 
 * Get current security settings
 */
export async function GET(request: NextRequest) {
  try {
    // Check admin authentication and permissions
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult;
    }

    const adminUtils = getAdminUtils();
    const settings = await adminUtils.getSecuritySettings();

    return NextResponse.json(settings);
  } catch (error) {
    console.error('Get security settings error:', error);
    return NextResponse.json(
      { error: 'Failed to load security settings' },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/admin/security/settings
 * 
 * Update security settings
 */
export async function PUT(request: NextRequest) {
  try {
    // Check admin authentication and permissions
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult;
    }

    const { user: currentUser } = authResult;

    if (!currentUser) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 401 }
      );
    }
    const settings = await request.json();

    // Validate settings
    const validationResult = validateSecuritySettings(settings);
    if (!validationResult.valid) {
      return NextResponse.json(
        { error: validationResult.error },
        { status: 400 }
      );
    }

    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();

    // Get current settings for comparison
    const currentSettings = await adminUtils.getSecuritySettings();

    // Update settings
    await adminUtils.updateSecuritySettings(settings);

    // Log the changes
    const changes = getSettingsChanges(currentSettings, settings);
    if (changes.length > 0) {
      await auditLogger.log(
        currentUser.user_id,
        'security.settings.update',
        'security_settings',
        {
          details: {
            changes,
            settingsUpdated: changes.map(c => c.setting)
          },
          request,
          ip_address: request.headers.get('x-forwarded-for') || 
                     request.headers.get('x-real-ip') || 
                     'unknown'
        }
      );
    }

    return NextResponse.json({
      message: 'Security settings updated successfully',
      changesCount: changes.length
    });
  } catch (error) {
    console.error('Update security settings error:', error);
    return NextResponse.json(
      { error: 'Failed to update security settings' },
      { status: 500 }
    );
  }
}

/**
 * Validate security settings
 */
function validateSecuritySettings(settings: any): { valid: boolean; error?: string } {
  // MFA settings validation
  if (settings.mfaEnforcement) {
    if (typeof settings.mfaEnforcement.gracePeriodDays !== 'number' || 
        settings.mfaEnforcement.gracePeriodDays < 0 || 
        settings.mfaEnforcement.gracePeriodDays > 30) {
      return { valid: false, error: 'MFA grace period must be between 0 and 30 days' };
    }
  }

  // Session security validation
  if (settings.sessionSecurity) {
    const { adminTimeoutMinutes, userTimeoutMinutes, maxConcurrentSessions } = settings.sessionSecurity;
    
    if (adminTimeoutMinutes < 5 || adminTimeoutMinutes > 480) {
      return { valid: false, error: 'Admin session timeout must be between 5 and 480 minutes' };
    }
    
    if (userTimeoutMinutes < 5 || userTimeoutMinutes > 1440) {
      return { valid: false, error: 'User session timeout must be between 5 and 1440 minutes' };
    }
    
    if (maxConcurrentSessions < 1 || maxConcurrentSessions > 10) {
      return { valid: false, error: 'Max concurrent sessions must be between 1 and 10' };
    }
  }

  // IP restrictions validation
  if (settings.ipRestrictions) {
    const { maxFailedAttempts, allowedRanges } = settings.ipRestrictions;
    
    if (maxFailedAttempts < 3 || maxFailedAttempts > 20) {
      return { valid: false, error: 'Max failed attempts must be between 3 and 20' };
    }
    
    // Validate IP ranges format
    if (allowedRanges && Array.isArray(allowedRanges)) {
      for (const range of allowedRanges) {
        if (!isValidIpRange(range)) {
          return { valid: false, error: `Invalid IP range format: ${range}` };
        }
      }
    }
  }

  // Monitoring settings validation
  if (settings.monitoring) {
    const { alertThresholds, logRetentionDays } = settings.monitoring;
    
    if (alertThresholds) {
      if (alertThresholds.failedLogins < 5 || alertThresholds.failedLogins > 100) {
        return { valid: false, error: 'Failed login threshold must be between 5 and 100' };
      }
      
      if (alertThresholds.suspiciousActivity < 3 || alertThresholds.suspiciousActivity > 50) {
        return { valid: false, error: 'Suspicious activity threshold must be between 3 and 50' };
      }
    }
    
    if (logRetentionDays < 30 || logRetentionDays > 365) {
      return { valid: false, error: 'Log retention must be between 30 and 365 days' };
    }
  }

  return { valid: true };
}

/**
 * Validate IP range format
 */
function isValidIpRange(range: string): boolean {
  // Simple validation for IP ranges (IPv4 CIDR notation)
  const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/;
  const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
  
  if (!cidrRegex.test(range) && !ipRegex.test(range)) {
    return false;
  }
  
  // Additional validation could be added here
  return true;
}

/**
 * Compare settings and return changes
 */
function getSettingsChanges(oldSettings: any, newSettings: any): Array<{setting: string, oldValue: any, newValue: any}> {
  const changes: Array<{setting: string, oldValue: any, newValue: any}> = [];
  
  function compareObjects(old: any, updated: any, path: string = '') {
    for (const key in updated) {
      const currentPath = path ? `${path}.${key}` : key;
      
      if (typeof updated[key] === 'object' && updated[key] !== null && !Array.isArray(updated[key])) {
        compareObjects(old[key] || {}, updated[key], currentPath);
      } else {
        if (JSON.stringify(old[key]) !== JSON.stringify(updated[key])) {
          changes.push({
            setting: currentPath,
            oldValue: old[key],
            newValue: updated[key]
          });
        }
      }
    }
  }
  
  compareObjects(oldSettings, newSettings);
  return changes;
}