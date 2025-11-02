import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
export async function POST(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    // Get the form data for file upload
    const formData = await request.formData();
    // Forward the request to the backend files upload endpoint
    const backendUrl = withBackendPath('/api/files/upload');
    const headers: HeadersInit = {};
    // Forward auth headers if present (don't set Content-Type for FormData)
    if (authorization) {
      headers['Authorization'] = authorization;
    }
    if (cookie) {
      headers['Cookie'] = cookie;
    }
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: formData,
      signal: AbortSignal.timeout(120000), // 2 minute timeout for file uploads

    const data = await response.json();
    // Return the backend response with appropriate status
    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }

  } catch (error) {
    // Return structured error response
    return NextResponse.json(
      { 
        error: 'File upload service unavailable',
        message: 'Unable to upload file',
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

}
