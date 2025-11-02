/**
 * User Statistics API Route
 * GET /api/admin/users/stats - Get user statistics for dashboard
 * 
 * Requirements: 4.6, 7.3
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse, UserStatistics } from '@/types/admin';
/**
 * GET /api/admin/users/stats - Get user statistics
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const adminUtils = getAdminDatabaseUtils();
    // Get current date for time-based calculations
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    // Get total user counts
    const totalUsersResult = await adminUtils.getUsersWithRoleFilter({});
    const totalUsers = totalUsersResult.pagination.total;
    // Get active users
    const activeUsersResult = await adminUtils.getUsersWithRoleFilter({ is_active: true });
    const activeUsers = activeUsersResult.pagination.total;
    // Get verified users
    const verifiedUsersResult = await adminUtils.getUsersWithRoleFilter({ is_verified: true });
    const verifiedUsers = verifiedUsersResult.pagination.total;
    // Get admin users (exclude super admins for regular admins)
    let adminUsersResult;
    let superAdminUsersResult;
    if (context.isSuperAdmin()) {
      adminUsersResult = await adminUtils.getUsersWithRoleFilter({ role: 'admin' });
      superAdminUsersResult = await adminUtils.getUsersWithRoleFilter({ role: 'super_admin' });
    } else {
      adminUsersResult = await adminUtils.getUsersWithRoleFilter({ role: 'admin' });
      superAdminUsersResult = { pagination: { total: 0 } };
    }
    const adminUsers = adminUsersResult.pagination.total;
    const superAdminUsers = superAdminUsersResult.pagination.total;
    // Get users created in different time periods
    const usersCreatedTodayResult = await adminUtils.getUsersWithRoleFilter({ 
      created_after: today 

    const usersCreatedToday = usersCreatedTodayResult.pagination.total;
    const usersCreatedThisWeekResult = await adminUtils.getUsersWithRoleFilter({ 
      created_after: weekAgo 

    const usersCreatedThisWeek = usersCreatedThisWeekResult.pagination.total;
    const usersCreatedThisMonthResult = await adminUtils.getUsersWithRoleFilter({ 
      created_after: monthAgo 

    const usersCreatedThisMonth = usersCreatedThisMonthResult.pagination.total;
    // Get users who logged in today
    const lastLoginTodayResult = await adminUtils.getUsersWithRoleFilter({ 
      last_login_after: today 

    const lastLoginToday = lastLoginTodayResult.pagination.total;
    // Get users with 2FA enabled
    const twoFactorEnabledResult = await adminUtils.getUsersWithRoleFilter({});
    const twoFactorEnabled = twoFactorEnabledResult.data.filter(user => user.two_factor_enabled).length;
    const statistics: UserStatistics = {
      total_users: totalUsers,
      active_users: activeUsers,
      verified_users: verifiedUsers,
      admin_users: adminUsers,
      super_admin_users: superAdminUsers,
      users_created_today: usersCreatedToday,
      users_created_this_week: usersCreatedThisWeek,
      users_created_this_month: usersCreatedThisMonth,
      last_login_today: lastLoginToday,
      two_factor_enabled: twoFactorEnabled
    };
    const response: AdminApiResponse<UserStatistics> = {
      success: true,
      data: statistics,
      meta: {
        generated_at: now.toISOString(),
        period_definitions: {
          today: today.toISOString(),
          week_ago: weekAgo.toISOString(),
          month_ago: monthAgo.toISOString()
        }
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'STATISTICS_FAILED',
        message: 'Failed to retrieve user statistics',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
