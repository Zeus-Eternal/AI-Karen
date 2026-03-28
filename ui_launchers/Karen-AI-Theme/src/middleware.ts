import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token =
    request.cookies.get('kari_session')?.value ||
    request.cookies.get('access_token')?.value;
  const pathname = request.nextUrl.pathname;

  // Define protected routes that require authentication
  const isProtectedRoute = pathname.startsWith('/dashboard') || 
                           pathname.startsWith('/chat') ||
                           pathname.startsWith('/settings') ||
                           pathname.startsWith('/admin');

  // If trying to access a protected route without a token, redirect to login
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', `${pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }

  // Also redirect root / to dashboard if logged in, otherwise to login
  if (pathname === '/') {
    if (token) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    } else {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

// Ensure the middleware only runs for relevant paths
export const config = {
  matcher: [
    '/',
    '/dashboard/:path*', 
    '/chat/:path*', 
    '/settings/:path*', 
    '/admin/:path*',
    '/login'
  ],
};
