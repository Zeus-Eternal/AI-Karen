import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/dashboard/stats
 * Returns comprehensive dashboard statistics
 */
export async function GET(request: NextRequest) {
  try {
    // In production, fetch from actual backend services
    // For now, generate realistic data

    const stats = {
      // User metrics
      totalUsers: Math.floor(Math.random() * 500) + 1000,
      activeUsers: Math.floor(Math.random() * 100) + 100,
      newUsersToday: Math.floor(Math.random() * 20) + 5,
      newUsersThisWeek: Math.floor(Math.random() * 100) + 50,

      // Message metrics
      totalMessages: Math.floor(Math.random() * 2000) + 8000,
      messagesToday: Math.floor(Math.random() * 500) + 200,
      messagesThisWeek: Math.floor(Math.random() * 2000) + 1500,
      avgMessagesPerUser: Math.floor(Math.random() * 10) + 15,

      // Performance metrics
      avgResponseTime: Math.floor(Math.random() * 200) + 200,
      p95ResponseTime: Math.floor(Math.random() * 300) + 400,
      p99ResponseTime: Math.floor(Math.random() * 400) + 600,

      // System health
      systemHealth: Math.random() > 0.1 ? 'healthy' : Math.random() > 0.5 ? 'degraded' : 'unhealthy',
      uptime: (99.5 + Math.random() * 0.5).toFixed(2),
      memoryUsage: Math.floor(Math.random() * 40) + 40,
      cpuUsage: Math.floor(Math.random() * 30) + 30,
      diskUsage: Math.floor(Math.random() * 30) + 50,

      // AI metrics
      totalConversations: Math.floor(Math.random() * 300) + 400,
      avgConversationLength: Math.floor(Math.random() * 5) + 8,
      totalTokensUsed: Math.floor(Math.random() * 1000000) + 5000000,
      totalCost: (Math.random() * 50 + 100).toFixed(2),

      // Engagement metrics
      dailyActiveUsers: Math.floor(Math.random() * 100) + 80,
      weeklyActiveUsers: Math.floor(Math.random() * 200) + 150,
      monthlyActiveUsers: Math.floor(Math.random() * 400) + 300,
      avgSessionDuration: Math.floor(Math.random() * 1000) + 1500, // seconds

      // Feature usage
      topFeatures: [
        { name: 'Chat', count: Math.floor(Math.random() * 1000) + 2000 },
        { name: 'Analytics', count: Math.floor(Math.random() * 500) + 800 },
        { name: 'Memory', count: Math.floor(Math.random() * 300) + 600 },
        { name: 'Extensions', count: Math.floor(Math.random() * 200) + 400 },
        { name: 'Admin', count: Math.floor(Math.random() * 100) + 200 },
      ],

      // Error metrics
      totalErrors: Math.floor(Math.random() * 20) + 10,
      errorRate: (Math.random() * 2 + 0.5).toFixed(2),
      criticalErrors: Math.floor(Math.random() * 3),

      // Trends (percentage changes from last period)
      trends: {
        users: (Math.random() * 20 - 5).toFixed(1),
        messages: (Math.random() * 30 - 10).toFixed(1),
        responseTime: (Math.random() * 10 - 15).toFixed(1), // negative is good
        activeUsers: (Math.random() * 15 - 3).toFixed(1),
      },

      // Real-time data
      currentActiveUsers: Math.floor(Math.random() * 50) + 20,
      requestsPerMinute: Math.floor(Math.random() * 100) + 80,

      // Timestamps
      timestamp: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
    };

    return NextResponse.json(stats, { status: 200 });
  } catch (error: any) {
    console.error('Dashboard stats error:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to fetch dashboard statistics',
        details: error.message,
      },
      { status: 500 }
    );
  }
}
