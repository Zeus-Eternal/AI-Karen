import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/engagement
 * Returns user engagement interaction data
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const range = searchParams.get("range") || "24h";
    const limit = parseInt(searchParams.get("limit") || "100");

    // Generate sample engagement data
    const interactions = [];
    const components = ["chat", "analytics", "memory", "grid", "chart", "admin"];
    const interactionTypes = ["click", "view", "hover", "input", "submit"];
    const users = ["user1", "user2", "user3", "user4", "user5"];

    for (let i = 0; i < Math.min(limit, 100); i++) {
      const ts = new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000);
      const componentType = components[Math.floor(Math.random() * components.length)];
      const interactionType = interactionTypes[Math.floor(Math.random() * interactionTypes.length)];
      const success = Math.random() > 0.1;

      interactions.push({
        id: `engagement_${i}_${Date.now()}`,
        timestamp: ts.toISOString(),
        userId: users[Math.floor(Math.random() * users.length)],
        componentType,
        componentId: `${componentType}_${Math.floor(Math.random() * 100)}`,
        interactionType,
        duration: Math.floor(Math.random() * 15000) + 100,
        success,
        errorMessage: success ? undefined : "Component interaction failed",
        sessionId: `session_${Math.floor(Math.random() * 10)}`,
        userAgent: "Mozilla/5.0 (Chrome)",
        location: "dashboard",
      });
    }

    // Sort by timestamp descending
    interactions.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    return NextResponse.json(
      {
        interactions,
        total: interactions.length,
        range,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Analytics engagement error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch engagement data",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
