import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.KAREN_BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://127.0.0.1:8000';

async function handleCopilotRequest(request: NextRequest) {
  try {
    const backendUrl = `${BACKEND_URL}/copilot/assist`;
    
    console.log(`[Copilot Proxy] ${request.method} ${backendUrl}`);
    
    // Get request body
    let body = undefined;
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      try {
        body = await request.text();
      } catch (e) {
        // Body might be empty
      }
    }
    
    // Forward headers
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    
    // Copy important headers
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    const sessionHeader = request.headers.get('x-session-id');
    if (sessionHeader) {
      headers['X-Session-ID'] = sessionHeader;
    }

    const conversationHeader = request.headers.get('x-conversation-id');
    if (conversationHeader) {
      headers['X-Conversation-ID'] = conversationHeader;
    }

    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    const userAgent = request.headers.get('user-agent');
    if (userAgent) {
      headers['User-Agent'] = userAgent;
    }
    
    // Use longer timeout for copilot requests
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000); // 2 minutes
    
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: { ...headers, Connection: 'keep-alive' },
      body: body || undefined,
      signal: controller.signal,
      // @ts-ignore undici option in Node runtime
      keepalive: true,
      cache: 'no-store',
    });
    
    clearTimeout(timeout);
    
    let data;
    const contentType = response.headers.get('content-type');
    
    if (contentType?.includes('application/json')) {
      try {
        const text = await response.text();
        if (text.trim() === '') {
          data = response.status >= 400 ? { error: 'Empty response from server' } : {};
        } else {
          data = JSON.parse(text);
        }
      } catch (error) {
        console.error(`JSON parsing error for copilot request:`, error);
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
    
    // Add CORS headers
    nextResponse.headers.set('Access-Control-Allow-Credentials', 'true');
    nextResponse.headers.set('Access-Control-Allow-Origin', '*');
    nextResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    nextResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Session-ID, X-Conversation-ID');
    
    return nextResponse;
    
  } catch (error) {
    console.error(`Copilot proxy error:`, error);
    console.error(`Backend URL: ${BACKEND_URL}`);
    
    let status = 500;
    let errorMessage = 'Internal server error';
    
    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.message.toLowerCase().includes('timeout')) {
        status = 504;
        errorMessage = 'Gateway timeout: copilot request took too long to respond.';
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

export async function GET(request: NextRequest) {
  return handleCopilotRequest(request);
}

export async function POST(request: NextRequest) {
  return handleCopilotRequest(request);
}

export async function PUT(request: NextRequest) {
  return handleCopilotRequest(request);
}

export async function DELETE(request: NextRequest) {
  return handleCopilotRequest(request);
}

export async function PATCH(request: NextRequest) {
  return handleCopilotRequest(request);
}

export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Session-ID, X-Conversation-ID',
      'Access-Control-Max-Age': '86400',
    },
  });
}