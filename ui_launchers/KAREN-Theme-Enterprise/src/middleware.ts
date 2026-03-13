import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Rate limiting store (in-memory for development - use Redis in production)
const rateLimit = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_MAX = 100; // Max requests per window
const RATE_LIMIT_WINDOW = 60000; // 1 minute in ms

// Get allowed origins from environment
const getAllowedOrigins = (): string[] => {
  const allowedOriginsEnv = process.env.ALLOWED_ORIGINS || '';
  if (allowedOriginsEnv) {
    return allowedOriginsEnv.split(',').map(origin => origin.trim());
  }
  
  // Default: localhost for development
  const isDev = process.env.NODE_ENV !== 'production';
  return isDev 
    ? ['http://localhost:3000', 'http://localhost:9002', 'http://localhost:3001']
    : []; // Production must explicitly set ALLOWED_ORIGINS
};

// Check if origin is allowed
const isOriginAllowed = (origin: string | null): boolean => {
  if (!origin) return false;
  const allowedOrigins = getAllowedOrigins();
  
  // In production, require explicit ALLOWED_ORIGINS configuration
  if (process.env.NODE_ENV === 'production' && allowedOrigins.length === 0) {
    console.error('SECURITY: ALLOWED_ORIGINS environment variable must be set in production');
    return false;
  }
  
  return allowedOrigins.includes(origin);
};

// Rate limiting check
const checkRateLimit = (identifier: string): boolean => {
  const now = Date.now();
  const record = rateLimit.get(identifier);
  
  if (!record || now > record.resetTime) {
    // Create new rate limit window
    rateLimit.set(identifier, {
      count: 1,
      resetTime: now + RATE_LIMIT_WINDOW
    });
    return true;
  }
  
  if (record.count >= RATE_LIMIT_MAX) {
    return false; // Rate limit exceeded
  }
  
  record.count++;
  return true;
};

// Get client identifier for rate limiting
const getClientIdentifier = (request: NextRequest): string => {
  // Use forwarded IP if available (behind reverse proxy)
  const forwarded = request.headers.get('x-forwarded-for');
  const ip = forwarded ? forwarded.split(',')[0].trim() : request.ip;
  return ip || 'unknown';
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const response = NextResponse.next();

  // ============================================================
  // SECURITY: Rate limiting for all routes
  // ============================================================
  const clientId = getClientIdentifier(request);
  if (!checkRateLimit(clientId)) {
    return new NextResponse(
      JSON.stringify({
        error: 'Too many requests',
        message: 'Rate limit exceeded. Please try again later.'
      }),
      {
        status: 429,
        headers: {
          'Content-Type': 'application/json',
          'Retry-After': '60'
        }
      }
    );
  }

  // Handle chunk loading errors by redirecting to a safe route
  if (pathname.includes('_next/static/chunks') && request.method === 'GET') {
    // Log the missing chunk for debugging
    // If it's a page chunk that's missing, we can try to regenerate it
    if (pathname.includes('/app/') && pathname.endsWith('.js')) {
      // Return a 404 response that Next.js can handle gracefully
      return new NextResponse(null, { status: 404 });
    }
  }

  // ============================================================
  // SECURITY: CORS restrictions for API routes
  // ============================================================
  if (pathname.startsWith('/api/')) {
    const origin = request.headers.get('origin');
    
    // Handle preflight OPTIONS requests
    if (request.method === 'OPTIONS') {
      if (isOriginAllowed(origin)) {
        return new NextResponse(null, {
          status: 200,
          headers: {
            'Access-Control-Allow-Origin': origin || '',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400' // 24 hours
          }
        });
      }
      return new NextResponse(null, { status: 403 }); // Forbidden origin
    }
    
    // Apply CORS for regular API requests
    if (isOriginAllowed(origin)) {
      response.headers.set('Access-Control-Allow-Origin', origin || '');
      response.headers.set('Access-Control-Allow-Credentials', 'true');
      response.headers.set('Access-Control-Expose-Headers', 'Content-Length, Content-Type');
    } else {
      // Origin not allowed
      return new NextResponse(
        JSON.stringify({
          error: 'Forbidden',
          message: 'Origin not allowed'
        }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
    
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    // Don't cache API responses by default
    response.headers.set('Cache-Control', 'no-store, must-revalidate');
    return response;
  }

  // Add performance and back/forward cache support headers
  // ============================================================
  // These headers help the browser cache pages for instant back/forward navigation
  // SECURITY: Add Content Security Policy
  // ============================================================
  if (!pathname.startsWith('/api/')) {
    // Content Security Policy
    const cspDirectives = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // unsafe-inline needed for Next.js dev mode
      "style-src 'self' 'unsafe-inline'", // unsafe-inline needed for styled-jsx
      "img-src 'self' data: https: blob:",
      "font-src 'self' data:",
      "connect-src 'self' https://api.yourdomain.com", // Replace with actual backend URL
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'"
    ].join('; ');
    
    response.headers.set('Content-Security-Policy', cspDirectives);
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    
    // Enable back/forward cache (bfcache) support
    response.headers.set('Cache-Control', 'public, max-age=0, must-revalidate');

    // Prevent unload handlers that block bfcache
    // Note: Your app should avoid using beforeunload/unload events

    // Add timing headers for performance monitoring
    response.headers.set('Server-Timing', 'middleware;dur=0');
  }

  // ============================================================
  // AUTHENTICATION: Protected routes
  // ============================================================
  // TODO: Implement authentication check for protected routes
  // Example: if (pathname.startsWith('/admin') && !isAuthenticated(request)) return redirectToLogin(request);
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
