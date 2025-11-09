// app/api/admin/users/import/route.ts
/**
 * User Import API Route
 * POST /api/admin/users/import - Import users from CSV or JSON file
 *
 * Requirements: 4.5, 4.6
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { validateEmail } from '@/lib/auth/setup-validation';
import type { AdminApiResponse } from '@/types/admin';

type RoleType = 'admin' | 'user';

interface ImportResult {
  imported_count: number;
  skipped_count: number;
  error_count: number;
  errors: Array<{
    row: number;
    email?: string;
    error: string;
  }>;
}

const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10MB
const MAX_ROWS = 5000; // server safety cap

function noStore(init?: ResponseInit): ResponseInit {
  return {
    ...(init || {}),
    headers: {
      ...(init?.headers || {}),
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
}

function getClientIP(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  if (forwarded) return forwarded.split(',')[0].trim();
  return request.headers.get('x-real-ip') || 'unknown';
}

/** Minimal RFC4180-ish CSV parser with quoted field support */
function parseCSV(text: string): { headers: string[]; rows: string[][] } {
  const rows: string[][] = [];
  let field = '';
  let inQuotes = false;
  let row: string[] = [];

  const pushField = () => {
    row.push(field);
    field = '';
  };
  const pushRow = () => {
    rows.push(row);
    row = [];
  };

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        // Possible escaped quote
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
    } else {
      if (c === '"') {
        inQuotes = true;
      } else if (c === ',') {
        pushField();
      } else if (c === '\n' || c === '\r') {
        // Normalize CRLF/CR/LF
        // If CRLF, skip the LF after CR
        if (c === '\r' && text[i + 1] === '\n') i++;
        pushField();
        pushRow();
      } else {
        field += c;
      }
    }
  }
  // Flush last field/row
  pushField();
  if (row.length > 1 || (row.length === 1 && row[0] !== '')) {
    pushRow();
  }

  if (rows.length === 0) return { headers: [], rows: [] };

  const headers = rows[0].map(h => h.trim().toLowerCase());
  const dataRows = rows.slice(1);
  return { headers, rows: dataRows };
}

function pickRole(raw?: string, fallback: RoleType = 'user'): RoleType {
  return raw?.toLowerCase() === 'admin' ? 'admin' : fallback;
}

function sanitizeString(v: unknown): string {
  if (typeof v !== 'string') return '';
  return v.trim();
}

async function parseCSVUsers(
  fileText: string,
  defaultRole: RoleType
): Promise<Array<{ email: string; full_name?: string; role?: RoleType }>> {
  const { headers, rows } = parseCSV(fileText);
  if (!headers.length) throw new Error('CSV has no header row');
  if (!headers.includes('email')) {
    throw new Error('CSV must contain an "email" column');
  }
  const idx = {
    email: headers.indexOf('email'),
    full_name: headers.indexOf('full_name'),
    name: headers.indexOf('name'),
    role: headers.indexOf('role'),
  };
  const users: Array<{ email: string; full_name?: string; role?: RoleType }> = [];

  for (let r = 0; r < rows.length; r++) {
    const row = rows[r];
    const email = sanitizeString(row[idx.email] ?? '');
    const full_name =
      sanitizeString(idx.full_name >= 0 ? row[idx.full_name] : '') ||
      sanitizeString(idx.name >= 0 ? row[idx.name] : '');
    const role = pickRole(idx.role >= 0 ? row[idx.role] : undefined, defaultRole);
    if (!email) continue; // skip empty
    users.push({ email, full_name, role });
    if (users.length >= MAX_ROWS) break;
  }
  return users;
}

async function parseJSONUsers(
  fileText: string,
  defaultRole: RoleType
): Promise<Array<{ email: string; full_name?: string; role?: RoleType }>> {
  let json: unknown;
  try {
    json = JSON.parse(fileText);
  } catch (e) {
    throw new Error('Invalid JSON format');
  }
  if (!Array.isArray(json)) {
    throw new Error('JSON must be an array of user objects');
  }
  const users = (json as any[]).slice(0, MAX_ROWS).map((item) => {
    const email = sanitizeString(item?.email);
    const full_name =
      sanitizeString(item?.full_name) || sanitizeString(item?.name);
    const role = pickRole(item?.role, defaultRole);
    return { email, full_name, role };
  });
  return users;
}

/**
 * POST /api/admin/users/import - Import users from file
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;
    const format = (formData.get('format') as string)?.toLowerCase() || 'csv';
    const skipDuplicates = formData.get('skip_duplicates') === 'true';
    const sendInvitations = formData.get('send_invitations') === 'true';
    const defaultRole = ((formData.get('default_role') as string) as RoleType) || 'user';

    if (!file) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'NO_FILE_PROVIDED',
            message: 'No file provided for import',
            details: {},
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    if (file.size > MAX_FILE_BYTES) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'FILE_TOO_LARGE',
            message: 'File size exceeds 10MB limit',
            details: { file_size: file.size },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    if (defaultRole === 'admin' && !context.isSuperAdmin()) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Super admin role required to import admin users',
            details: { requested_role: defaultRole, user_role: context.user.role },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 })
      );
    }

    const adminUtils = getAdminDatabaseUtils();
    const fileContent = await file.text();

    let userData: Array<{ email: string; full_name?: string; role?: RoleType }> = [];
    if (format === 'csv') {
      try {
        userData = await parseCSVUsers(fileContent, defaultRole);
      } catch (e) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'INVALID_CSV_FORMAT',
              message: e instanceof Error ? e.message : 'Invalid CSV',
              details: {},
            },
          } as AdminApiResponse<never>,
          noStore({ status: 400 })
        );
      }
    } else if (format === 'json') {
      try {
        userData = await parseJSONUsers(fileContent, defaultRole);
      } catch (e) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'INVALID_JSON_FORMAT',
              message: e instanceof Error ? e.message : 'Invalid JSON format',
              details: {},
            },
          } as AdminApiResponse<never>,
          noStore({ status: 400 })
        );
      }
    } else {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'UNSUPPORTED_FORMAT',
            message: 'Unsupported file format. Use CSV or JSON.',
            details: { format },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    // Guard against empty payloads
    if (!userData.length) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'NO_VALID_ROWS',
            message: 'No valid user rows found to import',
            details: {},
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    // Process import
    const result: ImportResult = {
      imported_count: 0,
      skipped_count: 0,
      error_count: 0,
      errors: [],
    };

    // Bulk import loop (sequential for simplicity; swap to batching if needed)
    for (let i = 0; i < userData.length; i++) {
      const user = userData[i];
      const rowNumber = i + 2; // CSV row index with header; good enough for JSON too

      try {
        // Validate email
        if (!user.email || !validateEmail(user.email)) {
          result.errors.push({
            row: rowNumber,
            email: user.email,
            error: 'Invalid email address',
          });
          result.error_count++;
          continue;
        }

        // Check duplicate
        const existing = await adminUtils.getUsersWithRoleFilter({ search: user.email });
        if (existing.data.length > 0) {
          if (skipDuplicates) {
            result.skipped_count++;
            continue;
          } else {
            result.errors.push({
              row: rowNumber,
              email: user.email,
              error: 'User already exists',
            });
            result.error_count++;
            continue;
          }
        }

        // Final role enforcement
        const finalRole: RoleType = (user.role || defaultRole);
        if (finalRole === 'admin' && !context.isSuperAdmin()) {
          result.errors.push({
            row: rowNumber,
            email: user.email,
            error: 'Insufficient permissions to create admin user',
          });
          result.error_count++;
          continue;
        }

        // Create user
        const userId = await adminUtils.createUserWithRole({
          email: user.email,
          full_name: user.full_name || '',
          role: finalRole,
          tenant_id: 'default',
          created_by: context.user.user_id,
        });

        // Audit creation
        await adminUtils.createAuditLog({
          user_id: context.user.user_id,
          action: 'user.import_create',
          resource_type: 'user',
          resource_id: userId,
          details: {
            email: user.email,
            role: finalRole,
            full_name: user.full_name || '',
            import_row: rowNumber,
            send_invitation: sendInvitations,
          },
          ip_address: getClientIP(request),
          user_agent: request.headers.get('user-agent') || undefined,
        });

        // Optional: invitation (left as explicit future hook)
        // if (sendInvitations) { await sendInvitationEmail(user.email, finalRole); }

        result.imported_count++;
      } catch (e) {
        result.errors.push({
          row: rowNumber,
          email: user.email,
          error: e instanceof Error ? e.message : 'Unknown error',
        });
        result.error_count++;
      }
    }

    // Audit completion
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'user.import_completed',
      resource_type: 'system',
      details: {
        file_name: file.name,
        file_size: file.size,
        format,
        total_rows: userData.length,
        imported_count: result.imported_count,
        skipped_count: result.skipped_count,
        error_count: result.error_count,
      },
      ip_address: getClientIP(request),
      user_agent: request.headers.get('user-agent') || undefined,
    });

    const response: AdminApiResponse<ImportResult> = {
      success: true,
      data: result,
      meta: {
        message: `Import completed: ${result.imported_count} imported, ${result.skipped_count} skipped, ${result.error_count} errors`,
        file_info: { name: file.name, size: file.size, format },
        import_settings: {
          skip_duplicates: skipDuplicates,
          send_invitations: sendInvitations,
          default_role: defaultRole,
          max_rows: MAX_ROWS,
        },
      },
    };

    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'IMPORT_FAILED',
          message: 'Failed to import users',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});
