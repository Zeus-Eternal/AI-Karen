/**
 * System Configuration API Routes
 * GET /api/admin/system/config - Get system configuration
 * PUT /api/admin/system/config - Update system configuration
 * 
 * Requirements: 3.6
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireSuperAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse, SystemConfig, SystemConfigUpdate } from '@/types/admin';
/**
 * GET /api/admin/system/config - Get system configuration (super admin only)
 */
export const GET = requireSuperAdmin(async (request: NextRequest, context) => {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category') || undefined;
    const adminUtils = getAdminDatabaseUtils();
    const configs = await adminUtils.getSystemConfig(category);
    // Group configurations by category
    const groupedConfigs = configs.reduce((acc, config) => {
      if (!acc[config.category]) {
        acc[config.category] = [];
      }
      acc[config.category].push(config);
      return acc;
    }, {} as Record<string, SystemConfig[]>);
    const response: AdminApiResponse<{ 
      configurations: SystemConfig[];
      grouped_configurations: Record<string, SystemConfig[]>;
      categories: string[];
    }> = {
      success: true,
      data: {
        configurations: configs,
        grouped_configurations: groupedConfigs,
        categories: Object.keys(groupedConfigs)
      },
      meta: {
        total_configurations: configs.length,
        filter_applied: category ? { category } : undefined,
        message: 'System configuration retrieved successfully'
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'SYSTEM_CONFIG_RETRIEVAL_FAILED',
        message: 'Failed to retrieve system configuration',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});

/**
 * PUT /api/admin/system/config - Update system configuration (super admin only)
 */
export const PUT = requireSuperAdmin(async (request: NextRequest, context) => {
  try {
    const body: Record<string, SystemConfigUpdate> = await request.json();
    if (!body || Object.keys(body).length === 0) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Configuration updates are required',
          details: { provided_keys: Object.keys(body) }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    const adminUtils = getAdminDatabaseUtils();
    const updatedConfigs: string[] = [];
    const errors: Record<string, string> = {};
    // Process each configuration update
    for (const [key, update] of Object.entries(body)) {
      try {
        // Validate configuration key exists
        const existingConfigs = await adminUtils.getSystemConfig();
        const existingConfig = existingConfigs.find(c => c.key === key);
        if (!existingConfig) {
          errors[key] = 'Configuration key not found';
          continue;
        }
        // Validate value type
        const expectedType = existingConfig.value_type;
        const providedValue = update.value;
        if (expectedType === 'number' && typeof providedValue !== 'number') {
          errors[key] = `Expected number, got ${typeof providedValue}`;
          continue;
        }
        if (expectedType === 'boolean' && typeof providedValue !== 'boolean') {
          errors[key] = `Expected boolean, got ${typeof providedValue}`;
          continue;
        }
        // Update configuration
        await adminUtils.updateSystemConfig(
          key,
          providedValue,
          context.user.user_id,
          update.description
        );
        updatedConfigs.push(key);
        // Log configuration change
        await adminUtils.createAuditLog({
          user_id: context.user.user_id,
          action: 'system_config.update',
          resource_type: 'system_config',
          resource_id: key,
          details: {
            key,
            previous_value: existingConfig.value,
            new_value: providedValue,
            previous_description: existingConfig.description,
            new_description: update.description,
            category: existingConfig.category
          },
          ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
          user_agent: request.headers.get('user-agent') || undefined
        });
      } catch (configError) {
        errors[key] = configError instanceof Error ? configError.message : 'Unknown error';
      }
    }
    // Check if any updates were successful
    if (updatedConfigs.length === 0 && Object.keys(errors).length > 0) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'SYSTEM_CONFIG_UPDATE_FAILED',
          message: 'No configurations were updated successfully',
          details: { errors, attempted_keys: Object.keys(body) }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Get updated configurations for response
    const updatedSystemConfigs = await adminUtils.getSystemConfig();
    const responseConfigs = updatedSystemConfigs.filter(c => updatedConfigs.includes(c.key));
    const response: AdminApiResponse<{
      updated_configurations: SystemConfig[];
      updated_keys: string[];
      errors?: Record<string, string>;
    }> = {
      success: true,
      data: {
        updated_configurations: responseConfigs,
        updated_keys: updatedConfigs,
        ...(Object.keys(errors).length > 0 && { errors })
      },
      meta: {
        message: `Successfully updated ${updatedConfigs.length} configuration(s)`,
        total_attempted: Object.keys(body).length,
        successful_updates: updatedConfigs.length,
        failed_updates: Object.keys(errors).length,
        ...(Object.keys(errors).length > 0 && {
          warning: 'Some configuration updates failed. Check the errors field for details.'
        })
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'SYSTEM_CONFIG_UPDATE_FAILED',
        message: 'Failed to update system configuration',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});
