import { NextRequest, NextResponse } from 'next/server';

// IMPORTANT: Do not default to the web UI port; that creates a proxy loop.
const backendUrl = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';

// For static export, we need to provide some common API paths that will be pre-generated
// This is a workaround since true catch-all routes can't be statically exported
export function generateStaticParams() {
  // Return common API paths that might be accessed during static generation
  return [
    { path: ['health'] },
    { path: ['auth', 'login'] },
    { path: ['auth', 'validate-session'] },
    { path: ['auth', 'logout'] },
    { path: ['auth', 'me'] },
    { path: ['auth', 'register'] },
    { path: ['chat'] },
    { path: ['chat', 'proxy'] },
    { path: ['chat', 'runtime'] },
    { path: ['chat', 'runtime', 'stream'] },
    { path: ['conversations'] },
    { path: ['conversations', 'create'] },
    { path: ['copilot', 'start'] },
    { path: ['dev-status'] },
    { path: ['extensions'] },
    { path: ['files'] },
    { path: ['files', 'upload'] },
    { path: ['models', 'all'] },
    { path: ['models', 'capabilities'] },
    { path: ['models', 'library'] },
    { path: ['models', 'load'] },
    { path: ['models', 'providers'] },
    { path: ['models', 'switch'] },
    { path: ['plugins'] },
    { path: ['providers', 'discovery'] },
    { path: ['ready'] },
    { path: ['metrics'] },
    { path: ['user', 'preferences', 'models'] },
    { path: ['system', 'config', 'models'] },
    { path: ['test-proxy'] },
  ];
}

async function handleRequest(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  try {
    // Safely resolve params with error handling
    let resolvedParams: { path: string[] };
    try {
      resolvedParams = await params;
    } catch (error) {
      return NextResponse.json(
        {
          error: 'Invalid request parameters',
          details: process.env.NODE_ENV === 'development' ? String(error) : undefined
        },
        { status: 400 }
      );
    }
    
    const path = resolvedParams.path?.join('/') || '';
    
    // Skip Next.js static files and other assets that should be handled by Next.js
    // Return early with proper 404 to let Next.js handle these
    if (path.startsWith('_next/') || path.startsWith('static/') || path.includes('.css') || path.includes('.js') || path.includes('.map') || path.includes('.woff') || path.includes('.woff2') || path.includes('.ttf') || path.includes('.eot') || path.includes('.svg') || path.includes('.png') || path.includes('.jpg') || path.includes('.jpeg') || path.includes('.gif') || path.includes('.ico')) {
      // Return 404 for static assets that should be handled by Next.js
      return NextResponse.json({ error: 'Not Found' }, { status: 404 });
    }
    
    // Skip page routes that should be handled by Next.js (not API calls)
    // These are requests for actual pages, not API endpoints
    // Note: 'models' is removed from here since /api/models/* are API endpoints, not pages
    const pageRoutes = ['login', 'signup', 'profile', 'admin', 'chat', 'setup', 'reset-password', 'verify-email', 'unauthorized', 'setup-2fa'];
    if (pageRoutes.includes(path) || pageRoutes.some(route => path.startsWith(route + '/'))) {
      return NextResponse.json({ error: 'Not Found' }, { status: 404 });
    }
    
    const url = new URL(request.url);
    const searchParams = url.searchParams.toString();
    const fullBackendUrl = `${backendUrl}/api/${path}${searchParams ? `?${searchParams}` : ''}`;
    
    // Get request body if it exists
    let body: string | undefined;
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      try {
        body = await request.text();
      } catch {
        // Body might be empty
      }
    }
    
    // Forward headers (excluding host and other problematic headers)
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    
    // Copy authorization header if present, else use auth_token cookie (set by our login route)
    const authHeader = request.headers.get('authorization');
    const authCookie = request.cookies.get('auth_token')?.value;
    const sessionCookie =
      request.cookies.get('kari_session')?.value ||
      request.cookies.get('session_token')?.value;
      
    if (authHeader) {
      headers['Authorization'] = authHeader;
    } else if (authCookie) {
      headers['Authorization'] = `Bearer ${authCookie}`;
    } else if (sessionCookie) {
      headers['Authorization'] = `Bearer ${sessionCookie}`;
    }
    
    // Forward cookies for HttpOnly session/refresh flows
    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }
    
    // Forward CSRF/XSRF tokens if your backend uses them
    const csrf = request.headers.get('x-csrf-token') || request.headers.get('x-xsrf-token');
    if (csrf) {
      headers['X-CSRF-Token'] = csrf;
      headers['X-XSRF-Token'] = csrf;
    }
    
    // Add user agent for better backend logging
    const userAgent = request.headers.get('user-agent');
    if (userAgent) {
      headers['User-Agent'] = userAgent;
    }
    
    // Add a conservative timeout to avoid hanging requests in dev
    // Increase timeout for provider endpoints, auth endpoints, model endpoints, and health checks that may take longer
    // Treat any '/providers/' '/models/' or '/health' path as potentially long-running (profiles, stats, suggestions, models, health)
    const isProviderEndpoint = /\/providers(\/|\b)/.test(request.url);
    const isAuthEndpoint = /\/auth(\/|\b)/.test(request.url);
    const isModelEndpoint = /\/models(\/|\b)/.test(request.url);
    const isHealthEndpoint = /\/health(\/|\b)/.test(request.url);
    
    // Allow override via env
    const SHORT_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_PROXY_TIMEOUT_MS || process.env.KAREN_API_PROXY_TIMEOUT_MS || 15000);
    const LONG_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_PROXY_LONG_TIMEOUT_MS || process.env.KAREN_API_PROXY_LONG_TIMEOUT_MS || 120000);
    const timeoutDuration = (isProviderEndpoint || isAuthEndpoint || isModelEndpoint || isHealthEndpoint) ? LONG_TIMEOUT_MS : SHORT_TIMEOUT_MS;
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutDuration);
    
    // Retry transient fetch errors (e.g., aborted/other side closed)
    const maxAttempts = (isProviderEndpoint || isAuthEndpoint || isModelEndpoint || isHealthEndpoint) ? 2 : 1;
    let response: Response | null = null;
    let lastError: unknown = null;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        response = await fetch(fullBackendUrl, {
          method: request.method,
          headers: { ...headers, Connection: 'keep-alive' },
          body: body || undefined,
          // Forward cookies if any (Next.js app routes run server-side)
          // Note: We intentionally do not set credentials here; cookies are forwarded via headers
          signal: controller.signal,
          keepalive: true,
          cache: 'no-store',
        });
        lastError = null;
        break;
      } catch (err: unknown) {
        lastError = err;
        // If aborted or UND_ERR_SOCKET and we have attempts left, small backoff
        const error = err as Error;
        const msg = String(error?.message || err);
        const isAbort = error?.name === 'AbortError';
        const isSocket = msg.includes('UND_ERR_SOCKET') || msg.includes('other side closed');
        if (attempt < maxAttempts && (isAbort || isSocket)) {
          await new Promise(res => setTimeout(res, 300));
          continue;
        }
        break;
      }
    }
    
    clearTimeout(timeout);
    
    if (!response) {
      throw lastError || new Error('Fetch failed without response');
    }
    
    // If upstream returned 404 for /api/auth/*, try simple-auth fallback /auth/*
    if (response.status === 404 && Array.isArray(resolvedParams.path) && resolvedParams.path[0] === 'auth') {
      const fallbackUrl = `${backendUrl}/auth/${resolvedParams.path.slice(1).join('/')}${searchParams ? `?${searchParams}` : ''}`;
      try {
        const fallbackResp = await fetch(fallbackUrl, {
          method: request.method,
          headers: { ...headers, Connection: 'keep-alive' },
          body: body || undefined,
          signal: controller.signal,
          keepalive: true,
          cache: 'no-store',
        });

        if (fallbackResp) {
          response = fallbackResp;
        }
      } catch {
        // ignore, will continue with original response
      }
    }
    
    let data: unknown;
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      try {
        const text = await response.text();
        if (text.trim() === '') {
          // Handle empty JSON responses
          data = response.status >= 400 ? { error: 'Empty response from server' } : {};
        } else {
          data = JSON.parse(text);
        }
      } catch {
        data = { error: 'Invalid JSON response from server' };
      }
    } else {
      data = await response.text();
    }
    
    // Create the response with proper status
    const nextResponse = NextResponse.json(
      typeof data === 'string' ? { error: data } : data, 
      { status: response.status }
    );
    
    // Forward important headers
    const headersToForward = ['set-cookie', 'cache-control', 'content-type', 'www-authenticate'];
    headersToForward.forEach(headerName => {
      const headerValue = response.headers.get(headerName);
      if (headerValue) {
        nextResponse.headers.set(headerName, headerValue);
      }
    });

    // Add CORS headers for better browser compatibility
    nextResponse.headers.set('Access-Control-Allow-Credentials', 'true');
    
    return nextResponse;
  } catch (error) {
    const resolvedParams = await params;
    console.error(`API proxy error for ${resolvedParams.path.join('/')}:`, error);
    
    // Provide more specific error information
    let status = 500;
    let errorMessage = 'Internal server error';
    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.message.toLowerCase().includes('aborted') || error.message.toLowerCase().includes('timeout')) {
        status = 504;
        errorMessage = 'Gateway timeout: backend took too long to respond.';
      } else if (error.message.includes('ECONNREFUSED')) {
        errorMessage = 'Backend server is not reachable. Please check if the backend is running.';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Failed to connect to backend server';
      } else {
        errorMessage = error.message;
      }
    }
    
    return NextResponse.json(
      { 
        error: errorMessage,
        details: process.env.NODE_ENV === 'development' ? error instanceof Error ? error.message : String(error) : undefined
      },
      { status }
    );
  }
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handleRequest(request, context);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handleRequest(request, context);
}

export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handleRequest(request, context);
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handleRequest(request, context);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return handleRequest(request, context);
}
