import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const response = NextResponse.next();

  // Handle chunk loading errors by redirecting to a safe route
  if (pathname.includes('_next/static/chunks') && request.method === 'GET') {
    // Log the missing chunk for debugging
    // If it's a page chunk that's missing, we can try to regenerate it
    if (pathname.includes('/app/') && pathname.endsWith('.js')) {
      // Return a 404 response that Next.js can handle gracefully
      return new NextResponse(null, { status: 404 });
    }
  }

  // Handle API routes - no authentication required
  if (pathname.startsWith('/api/')) {
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type');
    // Don't cache API responses by default
    response.headers.set('Cache-Control', 'no-store, must-revalidate');
    return response;
  }

  // Add performance and back/forward cache support headers
  // These headers help the browser cache pages for instant back/forward navigation
  if (!pathname.startsWith('/api/')) {
    // Enable back/forward cache (bfcache) support
    response.headers.set('Cache-Control', 'public, max-age=0, must-revalidate');

    // Prevent unload handlers that block bfcache
    // Note: Your app should avoid using beforeunload/unload events

    // Add timing headers for performance monitoring
    response.headers.set('Server-Timing', 'middleware;dur=0');
  }

  // No authentication checks - allow all requests
  return response;
}
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
