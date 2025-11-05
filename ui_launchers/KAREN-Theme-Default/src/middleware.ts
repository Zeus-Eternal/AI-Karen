import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
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
    const response = NextResponse.next();
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type');
    return response;
  }
  // No authentication checks - allow all requests
  return NextResponse.next();
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
