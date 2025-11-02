import { NextRequest, NextResponse } from 'next/server';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { FirstRunSetup, AdminApiResponse } from '@/types/admin';
/**
 * Check if this is the first run (no super admin exists)
 * GET /api/admin/setup/check-first-run
 */
export async function GET(request: NextRequest) {
  try {
    const adminUtils = getAdminDatabaseUtils();
    // Check if any super admin exists
    const existingSuperAdmins = await adminUtils.getUsersByRole('super_admin');
    const superAdminExists = existingSuperAdmins.length > 0;
    // Generate a setup token if this is first run
    let setupToken: string | undefined;
    if (!superAdminExists) {
      setupToken = generateSetupToken();
    }
    const setupData: FirstRunSetup = {
      super_admin_exists: superAdminExists,
      setup_completed: superAdminExists,
      setup_token: setupToken,
      system_info: {
        version: process.env.APP_VERSION || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
        setup_required: !superAdminExists
      }
    };
    const response: AdminApiResponse<FirstRunSetup> = {
      success: true,
      data: setupData,
      meta: {
        message: superAdminExists 
          ? 'System setup is complete' 
          : 'First-run setup required',
        timestamp: new Date().toISOString()
      }
    };
    return NextResponse.json(response, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }

  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'FIRST_RUN_CHECK_FAILED',
        message: 'Failed to check first-run status',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    }, { status: 500 });
  }
}
/**
 * Generate a secure setup token for first-run setup
 */
function generateSetupToken(): string {
  const timestamp = Date.now().toString();
  const randomBytes = Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  // Create token in expected format: setup_timestamp_randomhex
  return `setup_${timestamp}_${randomBytes}`;
}
/**
 * Verify setup token validity
 */
function verifySetupToken(token: string): {
  isValid: boolean;
  error?: string;
} {
  try {
    // Expected format: setup_timestamp_randomhex
    const parts = token.split('_');
    if (parts.length !== 3 || parts[0] !== 'setup') {
      return { isValid: false, error: 'Invalid token format' };
    }
    const timestamp = parseInt(parts[1]);
    if (isNaN(timestamp)) {
      return { isValid: false, error: 'Invalid token timestamp' };
    }
    // Check if token is expired (24 hours)
    const tokenAge = Date.now() - timestamp;
    if (tokenAge > 24 * 60 * 60 * 1000) {
      return { isValid: false, error: 'Setup token has expired' };
    }
    // Verify random hex part is valid
    const randomHex = parts[2];
    if (!/^[a-f0-9]{32}$/.test(randomHex)) {
      return { isValid: false, error: 'Invalid token format' };
    }
    return { isValid: true };
  } catch (error) {
    return { isValid: false, error: 'Invalid token format' };
  }
}
