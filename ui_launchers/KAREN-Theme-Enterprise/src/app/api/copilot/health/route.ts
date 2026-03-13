import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  return NextResponse.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    message: "Copilot API is healthy",
    routes: {
      assist: "/api/copilot/assist",
      lnm: {
        list: "/api/copilot/lnm/list",
        select: "/api/copilot/lnm/select"
      },
      plugins: {
        list: "/api/copilot/plugins/list",
        execute: "/api/copilot/plugins/execute"
      },
      security: {
        context: "/api/copilot/security/context"
      }
    }
  });
}