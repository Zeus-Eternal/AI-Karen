import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/dashboard/ai-insights
 * Returns AI-generated insights about system usage and trends
 */
export async function GET(request: NextRequest) {
  try {
    // In production, this would use AI/ML models to generate real insights
    // For now, generate sample insights based on patterns

    const insightTypes = ['trend', 'anomaly', 'recommendation', 'success'];
    const severities = ['info', 'warning', 'success', 'error'];

    const sampleInsights = [
      {
        type: 'trend',
        title: 'User Engagement Increasing',
        description: 'User engagement has increased by 18% this week compared to last week',
        severity: 'success',
      },
      {
        type: 'recommendation',
        title: 'Optimize Response Times',
        description: 'Consider implementing caching for frequently requested data to improve response times by up to 40%',
        severity: 'info',
      },
      {
        type: 'anomaly',
        title: 'Unusual Traffic Pattern',
        description: 'Detected 2.5x normal traffic at 3 PM - may indicate successful marketing campaign',
        severity: 'warning',
      },
      {
        type: 'success',
        title: 'System Performance Excellent',
        description: 'All systems operating at optimal performance with 99.98% uptime',
        severity: 'success',
      },
      {
        type: 'trend',
        title: 'Growing API Usage',
        description: 'API calls have grown 25% month-over-month, consider scaling infrastructure',
        severity: 'info',
      },
      {
        type: 'recommendation',
        title: 'Update User Onboarding',
        description: 'Users who complete tutorial are 3x more engaged - increase tutorial completion rate',
        severity: 'info',
      },
      {
        type: 'anomaly',
        title: 'Error Spike Detected',
        description: 'Error rate temporarily spiked to 3.2% at 2 AM but has since normalized',
        severity: 'warning',
      },
      {
        type: 'success',
        title: 'Cost Optimization Successful',
        description: 'Recent optimizations reduced infrastructure costs by 15% while maintaining performance',
        severity: 'success',
      },
    ];

    // Randomly select 3-5 insights
    const numInsights = Math.floor(Math.random() * 3) + 3;
    const selectedInsights = sampleInsights
      .sort(() => Math.random() - 0.5)
      .slice(0, numInsights)
      .map((insight, index) => ({
        id: `insight_${index}_${Date.now()}`,
        type: insight.type,
        title: insight.title,
        description: insight.description,
        severity: insight.severity,
        timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        confidence: (Math.random() * 30 + 70).toFixed(1), // 70-100% confidence
      }));

    return NextResponse.json(
      {
        insights: selectedInsights,
        totalInsights: selectedInsights.length,
        generatedAt: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error('AI Insights error:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to generate AI insights',
        details: error.message,
      },
      { status: 500 }
    );
  }
}
