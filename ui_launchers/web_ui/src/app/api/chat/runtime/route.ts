import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000';

export async function POST(request: NextRequest) {
  console.log('🔍 ChatRuntime API: Request received', {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries())
  });

  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    
    // Parse the request body for chat data
    const body = await request.json();

    console.log('🔍 ChatRuntime API: Request body parsed', {
      bodyKeys: Object.keys(body),
      model: body.model,
      messageCount: body.messages ? body.messages.length : 0,
      hasStream: body.stream !== undefined,
      bodyPreview: JSON.stringify(body).substring(0, 500) + (JSON.stringify(body).length > 500 ? '...' : '')
    });

    // Forward the request to the backend chat runtime endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const backendUrl = `${base}/api/chat/runtime`;

    console.log('🔍 ChatRuntime API: Backend URL constructed', {
      backendUrl,
      baseUrl: base
    });

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Forward auth headers if present
    if (authorization) {
      headers['Authorization'] = authorization;
      console.log('🔍 ChatRuntime API: Authorization header found', {
        hasAuth: true,
        authPrefix: authorization.substring(0, 20) + '...'
      });
    } else {
      console.log('🔍 ChatRuntime API: No authorization header');
    }
    if (cookie) {
      headers['Cookie'] = cookie;
      console.log('🔍 ChatRuntime API: Cookie header found', {
        hasCookie: true,
        cookiePrefix: cookie.substring(0, 50) + (cookie.length > 50 ? '...' : '')
      });
    } else {
      console.log('🔍 ChatRuntime API: No cookie header');
    }

    console.log('🔍 ChatRuntime API: Attempting backend fetch', {
      backendUrl,
      timeout: 60000,
      headers: Object.keys(headers)
    });

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60000), // 60 second timeout for chat processing
    });

    console.log('🔍 ChatRuntime API: Backend response received', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      ok: response.ok,
      url: response.url
    });

    const data = await response.json();

    console.log('🔍 ChatRuntime API: Backend response data', {
      dataKeys: Object.keys(data),
      hasContent: !!data.content,
      contentLength: data.content ? data.content.length : 0,
      hasError: !!data.error,
      error: data.error,
      dataPreview: JSON.stringify(data).substring(0, 500) + (JSON.stringify(data).length > 500 ? '...' : '')
    });

    // Return the backend response with appropriate status
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

  } catch (error) {
    console.error('🔍 ChatRuntime API: Error', error);
    
    // Return structured error response
    const errorResponse = {
      error: 'Chat service unavailable',
      message: 'Unable to process chat request',
      details: error instanceof Error ? error.message : 'Unknown error'
    };

    console.log('🔍 ChatRuntime API: Returning error response', errorResponse);
    return NextResponse.json(errorResponse, { status: 503 });
  }
}
