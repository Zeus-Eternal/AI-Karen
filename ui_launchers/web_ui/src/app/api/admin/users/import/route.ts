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
/**
 * POST /api/admin/users/import - Import users from file
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const format = formData.get('format') as string || 'csv';
    const skipDuplicates = formData.get('skip_duplicates') === 'true';
    const sendInvitations = formData.get('send_invitations') === 'true';
    const defaultRole = (formData.get('default_role') as 'admin' | 'user') || 'user';
    if (!file) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'NO_FILE_PROVIDED',
          message: 'No file provided for import',
          details: {}
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'FILE_TOO_LARGE',
          message: 'File size exceeds 10MB limit',
          details: { file_size: file.size }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Check permissions for creating admin users
    if (defaultRole === 'admin' && !context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Super admin role required to import admin users',
          details: { requested_role: defaultRole, user_role: context.user.role }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }
    const adminUtils = getAdminDatabaseUtils();
    const fileContent = await file.text();
    let userData: Array<{
      email: string;
      full_name?: string;
      role?: 'admin' | 'user';
    }> = [];
    // Parse file based on format
    if (format === 'csv') {
      const lines = fileContent.split('\n').filter(line => line.trim());
      const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
      // Validate headers
      if (!headers.includes('email')) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INVALID_CSV_FORMAT',
            message: 'CSV must contain an "email" column',
            details: { headers }
          }
        } as AdminApiResponse<never>, { status: 400 });
      }
      // Parse data rows
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''));
        const row: any = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || '';
        });
        if (row.email) {
          userData.push({
            email: row.email,
            full_name: row.full_name || row.name || '',
            role: (row.role === 'admin' ? 'admin' : 'user') as 'admin' | 'user'
          });
        }
      }
    } else if (format === 'json') {
      try {
        const jsonData = JSON.parse(fileContent);
        if (!Array.isArray(jsonData)) {
          throw new Error('JSON must be an array of user objects');
        }
        userData = jsonData.map(item => ({
          email: item.email,
          full_name: item.full_name || item.name || '',
          role: (item.role === 'admin' ? 'admin' : 'user') as 'admin' | 'user'
        }));
      } catch (parseError) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INVALID_JSON_FORMAT',
            message: 'Invalid JSON format',
            details: { error: parseError instanceof Error ? parseError.message : 'Parse error' }
          }
        } as AdminApiResponse<never>, { status: 400 });
      }
    } else {
      return NextResponse.json({
        success: false,
        error: {
          code: 'UNSUPPORTED_FORMAT',
          message: 'Unsupported file format. Use CSV or JSON.',
          details: { format }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Process import
    const result: ImportResult = {
      imported_count: 0,
      skipped_count: 0,
      error_count: 0,
      errors: []
    };
    for (let i = 0; i < userData.length; i++) {
      const user = userData[i];
      const rowNumber = i + 1;
      try {
        // Validate email
        if (!user.email || !validateEmail(user.email)) {
          result.errors.push({
            row: rowNumber,
            email: user.email,
            error: 'Invalid email address'
          });
          result.error_count++;
          continue;
        }
        // Check if user already exists
        const existingUsers = await adminUtils.getUsersWithRoleFilter({ search: user.email });
        if (existingUsers.data.length > 0) {
          if (skipDuplicates) {
            result.skipped_count++;
            continue;
          } else {
            result.errors.push({
              row: rowNumber,
              email: user.email,
              error: 'User already exists'
            });
            result.error_count++;
            continue;
          }
        }
        // Determine final role
        const finalRole = user.role || defaultRole;
        // Check permissions for admin role
        if (finalRole === 'admin' && !context.isSuperAdmin()) {
          result.errors.push({
            row: rowNumber,
            email: user.email,
            error: 'Insufficient permissions to create admin user'
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
          created_by: context.user.user_id
        });
        // Log user creation
        await adminUtils.createAuditLog({
          user_id: context.user.user_id,
          action: 'user.import_create',
          resource_type: 'user',
          resource_id: userId,
          details: {
            email: user.email,
            role: finalRole,
            full_name: user.full_name,
            import_row: rowNumber,
            send_invitation: sendInvitations
          },
          ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
          user_agent: request.headers.get('user-agent') || undefined
        });
        result.imported_count++;
        // TODO: Send invitation email if requested
        // if (sendInvitations) {
        //   await sendInvitationEmail(user.email, finalRole);
        // }
      } catch (error) {
        result.errors.push({
          row: rowNumber,
          email: user.email,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
        result.error_count++;
      }
    }
    // Log import completion
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
        error_count: result.error_count
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined
    });
    const response: AdminApiResponse<ImportResult> = {
      success: true,
      data: result,
      meta: {
        message: `Import completed: ${result.imported_count} users imported, ${result.skipped_count} skipped, ${result.error_count} errors`,
        file_info: {
          name: file.name,
          size: file.size,
          format
        },
        import_settings: {
          skip_duplicates: skipDuplicates,
          send_invitations: sendInvitations,
          default_role: defaultRole
        }
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'IMPORT_FAILED',
        message: 'Failed to import users',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});
