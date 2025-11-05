import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/realtime
 * Returns real-time system metrics
 */
export async function GET(request: NextRequest) {
  try {
    // In production, fetch real metrics from monitoring system
    // For now, generate realistic simulated data
    const metrics = {
      currentUsers: Math.floor(Math.random() * 50) + 10,
      requestsPerMinute: Math.floor(Math.random() * 200) + 50,
      avgLatency: Math.floor(Math.random() * 200) + 100,
      errorCount: Math.floor(Math.random() * 5),
      memoryUsageMB: Math.floor(Math.random() * 500) + 200,
      cpuUsage: Math.floor(Math.random() * 40) + 20,
      timestamp: new Date().toISOString(),
      uptime: Math.floor(Math.random() * 1000000) + 100000, // seconds
      activeConnections: Math.floor(Math.random() * 100) + 20,
      queueDepth: Math.floor(Math.random() * 50),
    };

    return NextResponse.json(metrics, { status: 200 });
  } catch (error: any) {
    console.error("Analytics realtime error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch realtime metrics",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
