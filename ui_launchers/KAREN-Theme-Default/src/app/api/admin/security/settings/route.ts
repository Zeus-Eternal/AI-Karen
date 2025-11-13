// ui_launchers/web_ui/src/app/api/admin/security/settings/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import type { SecuritySettings } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';

/**
 * GET /api/admin/security/settings
 * Fetch current security settings
 */
export async function GET(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult; // middleware already handled the response (e.g., 401/403)
    }

    const adminUtils = getAdminUtils();
    const settings = await adminUtils.getSecuritySettings();

    return NextResponse.json(settings, { status: 200 });
  } catch {
    return NextResponse.json(
      { error: 'Failed to load security settings' },
      { status: 500 },
    );
  }
}

/**
 * PUT /api/admin/security/settings
 * Update security settings (super_admin only)
 */
export async function PUT(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult; // middleware already returned a response
    }

    const { user: currentUser } = authResult ?? {};
    if (!currentUser?.user_id) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 401 },
      );
    }

    // Parse payload safely
    let incoming: unknown;
    try {
      incoming = await request.json();
    } catch {
      return NextResponse.json(
        { error: 'Invalid JSON payload' },
        { status: 400 },
      );
    }

    const payload = incoming as Partial<SecuritySettings>;

    // Validate
    const validation = validateSecuritySettings(payload);
    if (!validation.valid) {
      return NextResponse.json(
        { error: validation.error },
        { status: 400 },
      );
    }

    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();

    // Get prior state for diffing/audit
    const currentSettings = await adminUtils.getSecuritySettings();

    // Apply update
    await adminUtils.updateSecuritySettings(payload, currentUser.user_id);

    // Compute change set
    const changes = getSettingsChanges(currentSettings, payload);

    // Audit (only if anything actually changed)
    if (changes.length > 0) {
      await auditLogger.log(
        currentUser.user_id,
        'security.settings.update',
        'security_settings',
        {
          details: {
            changes,
            settingsUpdated: changes.map((c) => c.setting),
          },
          ip_address:
            request.headers.get('x-forwarded-for') ??
            request.headers.get('x-real-ip') ??
            'unknown',
          user_agent: request.headers.get('user-agent') ?? 'unknown',
        },
      );
    }

    return NextResponse.json(
      {
        message: 'Security settings updated successfully',
        changesCount: changes.length,
      },
      { status: 200 },
    );
  } catch {
    return NextResponse.json(
      { error: 'Failed to update security settings' },
      { status: 500 },
    );
  }
}

/**
 * Validation
 */
function validateSecuritySettings(
  settings: Partial<SecuritySettings>,
): { valid: true } | { valid: false; error: string } {
  // MFA
  if (settings.mfaEnforcement) {
    const { gracePeriodDays } = settings.mfaEnforcement;
    if (!isNumberInRange(gracePeriodDays, 0, 30)) {
      return invalid('MFA grace period must be between 0 and 30 days');
    }
  }

  // Session security
  if (settings.sessionSecurity) {
    const {
      adminTimeoutMinutes,
      userTimeoutMinutes,
      maxConcurrentSessions,
      sameSite,
    } = settings.sessionSecurity;

    if (!isNumberInRange(adminTimeoutMinutes, 5, 480)) {
      return invalid('Admin session timeout must be between 5 and 480 minutes');
    }
    if (!isNumberInRange(userTimeoutMinutes, 5, 1440)) {
      return invalid('User session timeout must be between 5 and 1440 minutes');
    }
    if (!isNumberInRange(maxConcurrentSessions, 1, 10)) {
      return invalid('Max concurrent sessions must be between 1 and 10');
    }
    if (sameSite && !['strict', 'lax', 'none'].includes(sameSite)) {
      return invalid('sameSite must be one of: strict, lax, none');
    }
  }

  // IP restrictions
  if (settings.ipRestrictions) {
    const { maxFailedAttempts, lockoutMinutes, allowedRanges, blockedRanges } =
      settings.ipRestrictions;

    if (!isNumberInRange(maxFailedAttempts, 3, 20)) {
      return invalid('Max failed attempts must be between 3 and 20');
    }
    if (lockoutMinutes !== undefined && !isNumberInRange(lockoutMinutes, 5, 1440)) {
      return invalid('Lockout minutes must be between 5 and 1440');
    }

    if (allowedRanges && !Array.isArray(allowedRanges)) {
      return invalid('allowedRanges must be an array of IP/CIDR strings');
    }
    if (blockedRanges && !Array.isArray(blockedRanges)) {
      return invalid('blockedRanges must be an array of IP/CIDR strings');
    }

    for (const list of [allowedRanges ?? [], blockedRanges ?? []]) {
      for (const range of list) {
        if (!isValidIpOrCidr(range)) {
          return invalid(`Invalid IP/CIDR format: ${range}`);
        }
      }
    }
  }

  // Monitoring
  if (settings.monitoring) {
    const { alertThresholds, logRetentionDays } = settings.monitoring;

    if (alertThresholds) {
      const { failedLogins, suspiciousActivity } = alertThresholds;
      if (!isNumberInRange(failedLogins, 5, 100)) {
        return invalid('Failed login threshold must be between 5 and 100');
      }
      if (!isNumberInRange(suspiciousActivity, 3, 50)) {
        return invalid('Suspicious activity threshold must be between 3 and 50');
      }
    }

    if (!isNumberInRange(logRetentionDays, 30, 365)) {
      return invalid('Log retention must be between 30 and 365 days');
    }
  }

  return { valid: true };
}

function invalid(error: string): { valid: false; error: string } {
  return { valid: false, error };
}

function isNumberInRange(n: unknown, min: number, max: number): n is number {
  return typeof n === 'number' && Number.isFinite(n) && n >= min && n <= max;
}

/**
 * IPv4 & CIDR validation (strict octet + mask bounds)
 */
function isValidIpOrCidr(input: string): boolean {
  const ipRegex =
    /^(25[0-5]|2[0-4]\d|1?\d?\d)\.(25[0-5]|2[0-4]\d|1?\d?\d)\.(25[0-5]|2[0-4]\d|1?\d?\d)\.(25[0-5]|2[0-4]\d|1?\d?\d)$/;
  const cidrRegex =
    /^(25[0-5]|2[0-4]\d|1?\d?\d)\.(25[0-5]|2[0-4]\d|1?\d?\d)\.(25[0-5]|2[0-4]\d|1?\d?\d)\.(25[0-5]|2[0-4]\d|1?\d?\d)\/([0-9]|[12][0-9]|3[0-2])$/;

  return ipRegex.test(input) || cidrRegex.test(input);
}

/**
 * Deep diff for audit (objects & arrays). Only reports keys present in `updated`.
 */
function getSettingsChanges(
  oldSettings: Record<string, unknown>,
  updatedSettings: Record<string, unknown>,
): Array<{ setting: string; oldValue: unknown; newValue: unknown }> {
  const changes: Array<{ setting: string; oldValue: unknown; newValue: unknown }> = [];

  const walk = (oldVal: unknown, newVal: unknown, path: string) => {
    const oldType = getType(oldVal);
    const newType = getType(newVal);

    if (newType === 'object' && oldType === 'object') {
      const keys = Object.keys(newVal);
      for (const k of keys) {
        walk(oldVal?.[k], newVal[k], path ? `${path}.${k}` : k);
      }
      return;
    }

    // For arrays and primitives, do a value compare
    const changed = !areValuesEqual(oldVal, newVal);
    if (changed) {
      changes.push({
        setting: path,
        oldValue: oldVal,
        newValue: newVal,
      });
    }
  };

  walk(oldSettings, updatedSettings, '');
  return changes;
}

function getType(v: unknown): 'array' | 'object' | 'null' | 'primitive' {
  if (Array.isArray(v)) return 'array';
  if (v === null) return 'null';
  if (typeof v === 'object') return 'object';
  return 'primitive';
}

function areValuesEqual(a: unknown, b: unknown): boolean {
  // Handle Date objects if they appear
  if (a instanceof Date && b instanceof Date) {
    return a.getTime() === b.getTime();
  }
  // Fast path for primitives
  if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) {
    return a === b;
  }
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    // Fallback if circular
    return false;
  }
}
