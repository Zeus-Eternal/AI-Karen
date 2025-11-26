// ui_launchers/web_ui/src/app/api/admin/setup/check-first-run/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { FirstRunSetup, AdminApiResponse } from '@/types/admin';

// Note: Removed 'force-dynamic' to allow static export

/**
 * Check if this is the first run (no super admin exists)
 * GET /api/admin/setup/check-first-run
 */
export async function GET(_request: NextRequest) {
  try {
    const adminUtils = getAdminDatabaseUtils();

    // Check if any super admin exists
    const existingSuperAdmins = await adminUtils.getUsersByRole('super_admin');
    const count = Array.isArray(existingSuperAdmins) ? existingSuperAdmins.length : 0;
    const superAdminExists = count > 0;

    // Generate a setup token only if this is first run
    let setupToken: string | undefined;
    if (!superAdminExists) {
      setupToken = await generateSetupToken(); // format: setup_<timestamp>_<32hex>
      const validation = verifySetupToken(setupToken);
      if (!validation.isValid) {
        throw new Error(validation.error ?? 'Generated invalid setup token');
      }
    }

    const setupData: FirstRunSetup = {
      super_admin_exists: superAdminExists,
      setup_completed: superAdminExists,
      setup_token: setupToken,
      system_info: {
        version: process.env.APP_VERSION || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
        setup_required: !superAdminExists,
      },
    };

    const response: AdminApiResponse<FirstRunSetup> = {
      success: true,
      data: setupData,
      meta: {
        message: superAdminExists ? 'System setup is complete' : 'First-run setup required',
        timestamp: new Date().toISOString(),
      },
    };

    return NextResponse.json(response, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'FIRST_RUN_CHECK_FAILED',
          message: 'Failed to check first-run status',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      },
      { status: 500 },
    );
  }
}

/**
 * Generate a secure setup token for first-run setup
 * Format: setup_<timestamp>_<32 hex chars>
 * TTL enforcement is performed by verifySetupToken (24h).
 */
async function generateSetupToken(): Promise<string> {
  const timestamp = Date.now();
  const randomHex = await getRandomHex(16); // 16 bytes → 32 hex chars
  return `setup_${timestamp}_${randomHex}`;
}

/**
 * Verify setup token validity (helper; keep in sync with generateSetupToken)
 */
function verifySetupToken(
  token: string,
): {
  isValid: boolean;
  error?: string;
} {
  try {
    // Expected format: setup_<timestamp>_<32 hex>
    const parts = token.split('_');
    if (parts.length !== 3 || parts[0] !== 'setup') {
      return { isValid: false, error: 'Invalid token format' };
    }

    const timestamp = Number(parts[1]);
    if (!Number.isFinite(timestamp)) {
      return { isValid: false, error: 'Invalid token timestamp' };
    }

    // 24h expiry
    const maxAgeMs = 24 * 60 * 60 * 1000;
    if (Date.now() - timestamp > maxAgeMs) {
      return { isValid: false, error: 'Setup token has expired' };
    }

    const randomHex = parts[2];
    if (!/^[a-f0-9]{32}$/.test(randomHex)) {
      return { isValid: false, error: 'Invalid token format' };
    }

    return { isValid: true };
  } catch {
    return { isValid: false, error: 'Invalid token format' };
  }
}

/** --------------------------
 * Local utilities
 * ------------------------- */

/**
 * Crypto-safe random bytes → hex string
 * Works in Edge runtime or Node 18+.
 */
async function getRandomHex(byteLen: number): Promise<string> {
  const bytes = new Uint8Array(byteLen);
  if (typeof globalThis.crypto?.getRandomValues === 'function') {
    globalThis.crypto.getRandomValues(bytes);
  } else {
    // Node fallback
    const nodeCrypto = await import('crypto');
    const buf = nodeCrypto.randomBytes(byteLen);
    for (let i = 0; i < byteLen; i++) bytes[i] = buf[i];
  }
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
