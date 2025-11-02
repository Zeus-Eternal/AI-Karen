import { NextResponse } from "next/server";

import { logger } from "@/lib/logger";

export async function POST() {
  logger.warn("Rejected request to deprecated /api/auth/dev-login endpoint");

  return NextResponse.json(
    {
      error: "This endpoint has been removed. Authenticate through the production login flow.",
    },
    { status: 410 },
  );
}

export async function GET() {
  logger.info("Health check against deprecated /api/auth/dev-login endpoint", {
    path: "/api/auth/dev-login",
  });

  return NextResponse.json(
    {
      message: "The development login endpoint has been decommissioned.",
      available: false,
    },
    { status: 410 },
  );
}