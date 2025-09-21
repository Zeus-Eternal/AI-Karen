import { NextResponse } from 'next/server';

// Development stub for copilot start when backend is unavailable
export async function POST() {
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Not available' }, { status: 404 });
  }
  return NextResponse.json({ status: 'ok', message: 'Copilot started (dev stub)' });
}
