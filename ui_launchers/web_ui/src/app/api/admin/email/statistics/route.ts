/**
 * Email Statistics API
 * 
 * API endpoint for retrieving email delivery statistics, analytics,
 * and performance metrics for admin monitoring.
 */
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { deliveryStatusManager } from '@/lib/email/delivery-tracker';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * GET /api/admin/email/statistics
 * Get email delivery statistics and analytics
 */
export async function GET(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { searchParams } = new URL(request.url);
    const startDate = searchParams.get('start_date') ? new Date(searchParams.get('start_date')!) : undefined;
    const endDate = searchParams.get('end_date') ? new Date(searchParams.get('end_date')!) : undefined;
    const templateId = searchParams.get('template_id') || undefined;
    // Validate date range
    if (startDate && endDate && startDate > endDate) {
      return NextResponse.json(
        { error: 'Start date must be before end date' },
        { status: 400 }
      );
    }
    // Get delivery statistics
    const statistics = await deliveryStatusManager.getDeliveryStatistics(
      startDate,
      endDate,
      templateId
    );
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_statistics_viewed',
      'email_statistics',
      {
        resourceId: undefined,
        details: { 
          start_date: startDate?.toISOString(),
          end_date: endDate?.toISOString(),
          template_id: templateId,
          total_sent: statistics.total_sent
        },
        request: request
      }
    );
    return NextResponse.json({
      success: true,
      data: {
        statistics,
        filters: {
          start_date: startDate?.toISOString(),
          end_date: endDate?.toISOString(),
          template_id: templateId,
        },
        generated_at: new Date().toISOString(),
      }

  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get email statistics' },
      { status: 500 }
    );
  }
}
