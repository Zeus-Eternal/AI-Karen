import { NextRequest } from 'next/server';

import { withBackendPath } from '@/app/api/_utils/backend';

export async function POST(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    
    // Parse the request body for chat data
    const body = await request.json();

    // Forward the request to the backend chat runtime stream endpoint
    const backendUrl = withBackendPath('/api/chat/runtime/stream');

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Forward auth headers if present
    if (authorization) {
      headers['Authorization'] = authorization;
    }
    if (cookie) {
      headers['Cookie'] = cookie;
    }

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120000), // 2 minute timeout for streaming
    });

    // For streaming responses, we need to handle differently
    if (response.headers.get('content-type')?.includes('text/event-stream') || 
        response.headers.get('content-type')?.includes('text/plain')) {
      
      // Return the streaming response directly
      return new Response(response.body, {
        status: response.status,
        headers: {
          'Content-Type': response.headers.get('content-type') || 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      });
    }

    // For non-streaming responses, parse as JSON
    const data = await response.json();
    return Response.json(data, { 
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

  } catch (error) {
    console.error('Chat stream error:', error);
    
    // Return structured error response
    return Response.json(
      { 
        error: 'Chat streaming service unavailable',
        message: 'Unable to process streaming chat request',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
}

// Handle preflight OPTIONS request for CORS
export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
