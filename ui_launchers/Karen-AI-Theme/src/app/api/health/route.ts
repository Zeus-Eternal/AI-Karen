import { NextRequest, NextResponse } from 'next/server';
import { proxyToBackend } from '../_lib/backend-proxy';

/**
 * Health Check Route
 *
 * Proxies health checks to the backend API to determine if services are ready.
 * This is used by the frontend to wait for backend initialization before
 * making other API calls.
 */
export const GET = async (request: Request) => {
  try {
    // Create a minimal NextRequest-like object for proxyToBackend
    const nextRequest = new NextRequest(request.url, {
      method: 'GET',
      headers: request.headers,
    });

    // Proxy the health check to the backend with a shorter timeout
    const response = await proxyToBackend(
      nextRequest,
      '/health',
      { longTimeout: false }
    );

    // If backend responds successfully, return success
    if (response.status === 200) {
      return NextResponse.json({ status: 'ok', backend_ready: true });
    }

    // If backend returns an error, proxy the error response
    return response;
  } catch (error) {
    console.warn('[HealthCheck] Backend not ready:', error);
    return NextResponse.json(
      {
        status: 'initializing',
        backend_ready: false,
        message: 'Backend services are still initializing'
      },
      { status: 503 } // Service Unavailable
    );
  }
};