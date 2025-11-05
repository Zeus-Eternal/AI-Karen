import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * GET /api/analytics/memory-network
 * Returns memory network graph data for visualization
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const range = searchParams.get("range") || "24h";

    // Generate sample memory network
    const clusters = ["work", "personal", "learning", "projects", "research"];
    const nodes = [];
    const edges = [];

    // Add cluster nodes
    for (const cluster of clusters) {
      nodes.push({
        id: `cluster_${cluster}`,
        label: cluster.charAt(0).toUpperCase() + cluster.slice(1),
        type: "cluster",
        size: Math.floor(Math.random() * 20) + 10,
        color: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
      });
    }

    // Add memory nodes
    const memoryCount = 50;
    for (let i = 0; i < memoryCount; i++) {
      const cluster = clusters[Math.floor(Math.random() * clusters.length)];
      nodes.push({
        id: `memory_${i}`,
        label: `Memory ${i}`,
        type: "memory",
        confidence: Math.random() * 0.4 + 0.6,
        cluster,
      });

      // Connect to cluster
      edges.push({
        from: `memory_${i}`,
        to: `cluster_${cluster}`,
        weight: Math.random(),
        type: "cluster",
      });

      // Random semantic connections to other memories
      if (Math.random() > 0.6 && i > 0) {
        const targetId = Math.floor(Math.random() * i);
        edges.push({
          from: `memory_${i}`,
          to: `memory_${targetId}`,
          weight: Math.random(),
          type: "semantic",
        });
      }
    }

    return NextResponse.json(
      {
        nodes,
        edges,
        clusters,
        totalMemories: memoryCount,
        range,
        timestamp: new Date().toISOString(),
      },
      { status: 200 }
    );
  } catch (error: any) {
    console.error("Analytics memory-network error:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to fetch memory network",
        details: error.message,
      },
      { status: 500 }
    );
  }
}
