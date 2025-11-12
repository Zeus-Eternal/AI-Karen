/**
 * Health Check API Endpoint
 * 
 * Proxies health check requests to the backend server to maintain consistency
 * with the backend health check format expected by the frontend.
 */

import { NextRequest, NextResponse } from 'next/server';

type BackendHealthData = Record<string, unknown> | string;

// Backend URL configuration
const BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * Main health check handler - proxies to backend
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    // Proxy the health check request to the backend
    const backendUrl = `${BACKEND_URL}/api/health`;
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
      cache: 'no-store',
    });
    
    clearTimeout(timeout);
    
    let data: BackendHealthData;
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      try {
        const text = await response.text();
        if (text.trim() === '') {
          data = response.status >= 400 ? { error: 'Empty response from server' } : {};
        } else {
          data = JSON.parse(text);
        }
      } catch (_error) {
        data = { error: 'Invalid JSON response from server' };
      }
    } else {
      data = await response.text();
    }
    
    // Return the backend response with the same status code
    return NextResponse.json(
      typeof data === 'string' ? { error: data } : data,
      { 
        status: response.status,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      }
    );
    
  } catch (error) {
    console.error('Health check proxy error:', error);
    
    // Return error response
    let status = 503;
    let errorMessage = 'Backend health check failed';
    
    if (error instanceof Error) {
      if (error.name === 'AbortError' || error.message.toLowerCase().includes('timeout')) {
        status = 504;
        errorMessage = 'Backend health check timeout';
      } else if (error.message.includes('ECONNREFUSED')) {
        errorMessage = 'Backend server is not reachable';
      } else if (error.message.includes('fetch')) {
        errorMessage = 'Failed to connect to backend server';
      } else {
        errorMessage = error.message;
      }
    }
    
    return NextResponse.json(
      {
        status: 'unhealthy',
        error: errorMessage,
        timestamp: new Date().toISOString(),
        details: process.env.NODE_ENV === 'development' ? error instanceof Error ? error.message : String(error) : undefined
      },
      { 
        status,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      }
    );
  }
}