import { NextRequest } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
// Simple fallback responses for degraded mode
const FALLBACK_RESPONSES = [
  "I'm currently running in degraded mode due to backend connectivity issues. I can provide basic assistance, but my full AI capabilities are temporarily limited.",
  "The system is experiencing some connectivity issues. I'm operating with reduced functionality but can still help with basic questions.",
  "I'm currently in fallback mode. While I can't access my full AI capabilities right now, I'm still here to help with what I can.",
  "The backend services are temporarily unavailable. I'm running in a limited capacity but can still provide some assistance.",
  "I'm operating in degraded mode due to system issues. My responses may be limited, but I'll do my best to help you."
];
function createFallbackResponse(userMessage: string): string {
  // Simple keyword-based responses for common queries
  const message = userMessage.toLowerCase();
  if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
    return "Hello! I'm currently running in degraded mode, but I'm still here to help. What can I assist you with?";
  }
  if (message.includes('help') || message.includes('what can you do')) {
    return "I'm currently in degraded mode with limited capabilities. I can provide basic information and assistance, but my full AI features are temporarily unavailable due to backend connectivity issues.";
  }
  if (message.includes('error') || message.includes('problem') || message.includes('issue')) {
    return "I can see you're experiencing an issue. I'm currently running in degraded mode, so my troubleshooting capabilities are limited. Please try again later when full services are restored.";
  }
  if (message.includes('status') || message.includes('health')) {
    return "The system is currently in degraded mode due to backend connectivity issues. Core services are running but AI capabilities are limited. Please check back later for full functionality.";
  }
  // Default fallback response
  const randomResponse = FALLBACK_RESPONSES[Math.floor(Math.random() * FALLBACK_RESPONSES.length)];
  return randomResponse;
}
function createStreamingFallbackResponse(message: string): ReadableStream {
  const response = createFallbackResponse(message);
  return new ReadableStream({
    start(controller) {
      // Simulate streaming by sending chunks
      const chunks = response.split(' ');
      let index = 0;
      const sendChunk = () => {
        if (index < chunks.length) {
          const chunk = index === 0 ? chunks[index] : ' ' + chunks[index];
          controller.enqueue(new TextEncoder().encode(`data: ${JSON.stringify({ content: chunk })}\n\n`));
          index++;
          setTimeout(sendChunk, 50); // Simulate typing delay
        } else {
          controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
          controller.close();
        }
      };
      sendChunk();
    }

}
async function checkDegradedMode(): Promise<boolean> {
  try {
    const response = await fetch('/api/health/degraded-mode', {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3000)

    if (response.ok) {
      const data = await response.json();
      return data.is_active || data.degraded_mode;
    }
  } catch (error) {
  }
  return false; // Default to not degraded if check fails
}
export async function POST(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    // Parse the request body for chat data
    const body = await request.json();
    // Check if we should use fallback mode
    const isDegraded = await checkDegradedMode();
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
    try {
      const response = await fetch(backendUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(isDegraded ? 10000 : 120000), // Shorter timeout in degraded mode

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

    } catch (backendError) {
      // Use fallback response when backend is unavailable
      const userMessage = body.messages?.[body.messages.length - 1]?.content || body.message || '';
      // Return streaming fallback response
      return new Response(createStreamingFallbackResponse(userMessage), {
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },

    }
  } catch (error) {
    // Return fallback response even for parsing errors
    try {
      const fallbackMessage = "I'm experiencing technical difficulties and am running in emergency fallback mode. Please try again later.";
      return new Response(createStreamingFallbackResponse(fallbackMessage), {
        status: 200,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },

    } catch (fallbackError) {
      // Last resort: return JSON error
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

}
