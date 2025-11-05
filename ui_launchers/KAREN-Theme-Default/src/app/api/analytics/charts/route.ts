import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/charts
 * Returns chart data and statistics for analytics visualizations
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const range = searchParams.get("range") || "24h";

    // Calculate data points based on range
    const points =
      range === "1h" ? 60 : range === "24h" ? 24 : range === "7d" ? 7 : range === "30d" ? 30 : 90;

    // Generate time series data
    const timeseries = [];
    const now = new Date();
    const providers = ["openai", "anthropic", "local"];

    for (let i = 0; i < points; i++) {
      const offset =
        range === "1h"
          ? i * 60 * 1000
          : range === "24h"
          ? i * 60 * 60 * 1000
          : i * 24 * 60 * 60 * 1000;
      const timestamp = new Date(now.getTime() - (points - i) * offset);

      timeseries.push({
        timestamp: timestamp.toISOString(),
        messageCount: Math.floor(Math.random() * 50) + 10,
        responseTime: Math.floor(Math.random() * 300) + 100,
        userSatisfaction: Math.random() * 2 + 3,
        aiInsights: Math.floor(Math.random() * 20) + 5,
        tokenUsage: Math.floor(Math.random() * 5000) + 1000,
        llmProvider: providers[Math.floor(Math.random() * providers.length)],
      });
    }

    // Calculate statistics
    const totalMessages = timeseries.reduce((sum, d) => sum + d.messageCount, 0);
    const avgResponseTime = Math.round(
      timeseries.reduce((sum, d) => sum + d.responseTime, 0) / timeseries.length
    );
    const avgSatisfaction =
      timeseries.reduce((sum, d) => sum + d.userSatisfaction, 0) / timeseries.length;
    const totalInsights = timeseries.reduce((sum, d) => sum + d.aiInsights, 0);

    // Count provider usage
    const providerCounts: Record<string, number> = {};
    timeseries.forEach((d) => {
      providerCounts[d.llmProvider] = (providerCounts[d.llmProvider] || 0) + 1;
    });

    const topLlmProviders = Object.entries(providerCounts)
      .map(([provider, count]) => ({ provider, count }))
      .sort((a, b) => b.count - a.count);

    const stats = {
      totalConversations: Math.floor(totalMessages / 15),
      totalMessages,
      avgResponseTime,
      avgSatisfaction,
      totalInsights,
      activeUsers: Math.floor(Math.random() * 50) + 120,
      topLlmProviders,
    };

    return NextResponse.json(
      {
        timeseries,
        stats,
        range,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Analytics charts error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch chart data",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
