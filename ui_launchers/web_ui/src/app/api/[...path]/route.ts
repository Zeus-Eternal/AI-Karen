import { NextRequest, NextResponse } from 'next/server';

// IMPORTANT: Do not default to the web UI port; that creates a proxy loop.
const BACKEND_URL =
  process.env.KAREN_BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://127.0.0.1:8000';

async function handleRequest(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  try {
    const resolvedParams = await params;
    const path = resolvedParams.path.join('/');
    const url = new URL(request.url);
    const searchParams = url.searchParams.toString();
    const backendUrl = `${BACKEND_URL}/api/${path}${searchParams ? `?${searchParams}` : ''}`;
    
    // Log the request for debugging
    console.log(`[API Proxy] ${request.method} ${backendUrl}`);
    
    // Get request body if it exists
    let body = undefined;
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      try {
        body = await request.text();
      } catch (e) {
        // Body might be empty
      }
    }
    
    // Forward headers (excluding host and other problematic headers)
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    
    // Copy authorization header if present
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
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
    // Increase timeout for provider endpoints that may take longer
    const isProviderEndpoint = request.url.includes('/providers/') && request.url.includes('/suggestions');
    const timeoutDuration = isProviderEndpoint ? 30000 : 15000; // 30s for provider endpoints, 15s for others
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutDuration);
    const response = await fetch(backendUrl, {
      method: request.method,
      headers,
      body: body || undefined,
      // Forward cookies if any (Next.js app routes run server-side)
      // Note: We intentionally do not set credentials here; cookies are forwarded via headers
      signal: controller.signal,
    });
    clearTimeout(timeout);
    
    let data;
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
      } catch (error) {
        console.error(`JSON parsing error for ${response.url}:`, error);
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
    console.error(`Backend URL: ${BACKEND_URL}`);
    
    // Provide more specific error information
    let errorMessage = 'Internal server error';
    if (error instanceof Error) {
      if (error.message.includes('ECONNREFUSED')) {
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
      { status: 500 }
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
