import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/summary
 * Returns analytics summary statistics for the dashboard
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const range = searchParams.get("range") || "24h";

    // In production, fetch real data from backend
    // For now, return sample data with realistic variations
    const summary = {
      totalInteractions: Math.floor(Math.random() * 500) + 1000,
      activeUsers: Math.floor(Math.random() * 50) + 120,
      avgResponseTime: Math.floor(Math.random() * 100) + 300,
      memoryNodes: Math.floor(Math.random() * 300) + 1700,
      totalMessages: Math.floor(Math.random() * 1000) + 8000,
      errorRate: (Math.random() * 2 + 1).toFixed(1),
      satisfaction: (Math.random() * 0.5 + 4.5).toFixed(1),
      peakHour: `${Math.floor(Math.random() * 10) + 10}:00`,
      range,
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(summary, { status: 200 });
  } catch (error: any) {
    console.error("Analytics summary error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch analytics summary",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
