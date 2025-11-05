// app/api/admin/users/stats/route.ts
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

/**
 * GET /api/admin/users/stats - Get user statistics
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const adminUtils = getAdminDatabaseUtils();

    // Period anchors (UTC-normalized start-of-day)
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Fire queries in parallel to minimize wall time
    const [
      totalUsersResult,
      activeUsersResult,
      verifiedUsersResult,
      adminUsersResult,
      superAdminUsersResultOrZero,
      usersCreatedTodayResult,
      usersCreatedThisWeekResult,
      usersCreatedThisMonthResult,
      lastLoginTodayResult,
      usersFor2FA // may be large; consider adding a dedicated filter in adminUtils later
    ] = await Promise.all([
      adminUtils.getUsersWithRoleFilter({}),
      adminUtils.getUsersWithRoleFilter({ is_active: true }),
      adminUtils.getUsersWithRoleFilter({ is_verified: true }),
      adminUtils.getUsersWithRoleFilter({ role: 'admin' }),
      (async () => {
        if (context.isSuperAdmin()) {
          return adminUtils.getUsersWithRoleFilter({ role: 'super_admin' });
        }
        // For non-super admins, never reveal super_admin counts
        return { pagination: { total: 0 } } as any;
      })(),
      adminUtils.getUsersWithRoleFilter({ created_after: today }),
      adminUtils.getUsersWithRoleFilter({ created_after: weekAgo }),
      adminUtils.getUsersWithRoleFilter({ created_after: monthAgo }),
      adminUtils.getUsersWithRoleFilter({ last_login_after: today }),
      adminUtils.getUsersWithRoleFilter({}), // fallback to filter locally for 2FA
    ]);

    const totalUsers = totalUsersResult.pagination.total;
    const activeUsers = activeUsersResult.pagination.total;
    const verifiedUsers = verifiedUsersResult.pagination.total;
    const adminUsers = adminUsersResult.pagination.total;

    // Respect RBAC: non-super admins get 0 here by design above
    const superAdminUsers =
      (superAdminUsersResultOrZero as any).pagination?.total ?? 0;

    const usersCreatedToday = usersCreatedTodayResult.pagination.total;
    const usersCreatedThisWeek = usersCreatedThisWeekResult.pagination.total;
    const usersCreatedThisMonth = usersCreatedThisMonthResult.pagination.total;

    const lastLoginToday = lastLoginTodayResult.pagination.total;

    // If your backend supports filtering by two_factor_enabled, switch to:
    // const twoFactorEnabled = (await adminUtils.getUsersWithRoleFilter({ two_factor_enabled: true })).pagination.total;
    const twoFactorEnabled = Array.isArray(usersFor2FA.data)
      ? usersFor2FA.data.filter((u: any) => u.two_factor_enabled).length
      : 0;

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
      two_factor_enabled: twoFactorEnabled,
    };

    const response: AdminApiResponse<UserStatistics> = {
      success: true,
      data: statistics,
      meta: {
        generated_at: now.toISOString(),
        period_definitions: {
          today: today.toISOString(),
          week_ago: weekAgo.toISOString(),
          month_ago: monthAgo.toISOString(),
        },
      },
    };

    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'STATISTICS_FAILED',
          message: 'Failed to retrieve user statistics',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 }),
    );
  }
});
