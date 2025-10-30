import { NextResponse } from 'next/server';

import { logger } from '@/lib/logger';

// Explicitly disable the legacy development bypass in production builds.
export async function POST() {
  logger.warn('Rejected request to deprecated /api/auth/dev-bypass endpoint');

  return NextResponse.json(
    {
      error: 'This endpoint has been removed. Use the standard authentication flow.',
    },
    { status: 410 },
  );
}