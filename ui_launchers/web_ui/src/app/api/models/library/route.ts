import { NextResponse } from 'next/server';

// Development stub for models library when backend route is unavailable
export async function GET() {
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Not available' }, { status: 404 });
  }
  // Dev-only: Return an empty library so the UI can render without errors
  return NextResponse.json({ models: [], sources: [], available: 0 });
}
