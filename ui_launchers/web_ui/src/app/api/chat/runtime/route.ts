import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
const isVerboseLogging = process.env.NODE_ENV !== 'production';
// Simple fallback responses for degraded mode
function createFallbackResponse(userMessage: string): any {
  // Simple keyword-based responses for common queries
  const message = userMessage.toLowerCase();
  if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
    return {
      content: "Hello! I'm currently running in degraded mode, but I'm still here to help. What can I assist you with?",
      role: 'assistant',
      model: 'fallback-mode',
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
    };
  }
  if (message.includes('help') || message.includes('what can you do')) {
    return {
      content: "I'm currently in degraded mode with limited capabilities. I can provide basic information and assistance, but my full AI features are temporarily unavailable due to backend connectivity issues.",
      role: 'assistant',
      model: 'fallback-mode',
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
    };
  }
  if (message.includes('error') || message.includes('problem') || message.includes('issue')) {
    return {
      content: "I can see you're experiencing an issue. I'm currently running in degraded mode, so my troubleshooting capabilities are limited. Please try again later when full services are restored.",
      role: 'assistant',
      model: 'fallback-mode',
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
    };
  }
  if (message.includes('status') || message.includes('health')) {
    return {
      content: "The system is currently in degraded mode due to backend connectivity issues. Core services are running but AI capabilities are limited. Please check back later for full functionality.",
      role: 'assistant',
      model: 'fallback-mode',
      usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
    };
  }
  // Default fallback response
  return {
    content: "I'm currently running in degraded mode due to backend connectivity issues. I can provide basic assistance, but my full AI capabilities are temporarily limited. Please try again later for full functionality.",
    role: 'assistant',
    model: 'fallback-mode',
    usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 }
  };
}
async function checkDegradedMode(): Promise<boolean> {
  try {
    const response = await fetch('/api/health/degraded-mode', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000)
    });
    if (response.ok) {
      const data = await response.json();
      return data.is_active || data.degraded_mode;
    }
  } catch (error) {
  }
  return false; // Default to not degraded if check fails
}
export async function POST(request: NextRequest) {
  if (isVerboseLogging) {
    console.log('🔍 ChatRuntime API: Request received', {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries())
    });
  }
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    // Parse the request body for chat data
    const body = await request.json();
    if (isVerboseLogging) {
      console.log('🔍 ChatRuntime API: Request body parsed', {
        bodyKeys: Object.keys(body),
        model: body.model,
        messageCount: body.messages ? body.messages.length : 0,
        hasStream: body.stream !== undefined,
        bodyPreview: JSON.stringify(body).substring(0, 500) + (JSON.stringify(body).length > 500 ? '...' : '')
      });
    }
    // Check if we should use fallback mode
    const isDegraded = await checkDegradedMode();
    // Forward the request to the backend chat runtime endpoint
    const backendUrl = withBackendPath('/api/chat/runtime');
    const resolvedBase = backendUrl.replace(/\/api\/chat\/runtime$/, '');
    if (isVerboseLogging) {
    }
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    // Forward auth headers if present
    if (authorization) {
      headers['Authorization'] = authorization;
      if (isVerboseLogging) {
        console.log('🔍 ChatRuntime API: Authorization header found', {
          hasAuth: true,
          authPrefix: authorization.substring(0, 20) + '...'
        });
      }
    } else if (isVerboseLogging) {
    }
    if (cookie) {
      headers['Cookie'] = cookie;
      if (isVerboseLogging) {
        console.log('🔍 ChatRuntime API: Cookie header found', {
          hasCookie: true,
          cookiePrefix: cookie.substring(0, 50) + (cookie.length > 50 ? '...' : '')
        });
      }
    } else if (isVerboseLogging) {
    }
    if (isVerboseLogging) {
      });
    }
    try {
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(isDegraded ? 10000 : 60000), // Shorter timeout in degraded mode
      });
      if (isVerboseLogging) {
        console.log('🔍 ChatRuntime API: Backend response received', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          ok: response.ok,
          url: response.url
        });
      }
      const data = await response.json();
      if (isVerboseLogging) {
        console.log('🔍 ChatRuntime API: Backend response data', {
          dataKeys: Object.keys(data),
          hasContent: !!data.content,
          contentLength: data.content ? data.content.length : 0,
          hasError: !!data.error,
          error: data.error,
          dataPreview: JSON.stringify(data).substring(0, 500) + (JSON.stringify(data).length > 500 ? '...' : '')
        });
      }
      // Return the backend response with appropriate status
      return NextResponse.json(data, {
        status: response.status,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
    } catch (backendError) {
      // Use fallback response when backend is unavailable
      const userMessage = body.messages?.[body.messages.length - 1]?.content || body.message || '';
      const fallbackData = createFallbackResponse(userMessage);
      if (isVerboseLogging) {
      }
      return NextResponse.json(fallbackData, {
        status: 200,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
    }
  } catch (error) {
    // Return fallback response even for parsing errors
    try {
      const fallbackData = createFallbackResponse("I'm experiencing technical difficulties and am running in emergency fallback mode. Please try again later.");
      if (isVerboseLogging) {
      }
      return NextResponse.json(fallbackData, { 
        status: 200,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
    } catch (fallbackError) {
      // Last resort: return JSON error
      const errorResponse = {
        error: 'Chat service unavailable',
        message: 'Unable to process chat request',
        details: error instanceof Error ? error.message : 'Unknown error'
      };
      if (isVerboseLogging) {
      }
      return NextResponse.json(errorResponse, { status: 503 });
    }
  }
}
