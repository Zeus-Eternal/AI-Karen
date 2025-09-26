import { NextRequest, NextResponse } from 'next/server';

// Use the correct backend URL from environment variables
const BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://127.0.0.1:8000';
const TIMEOUT_MS = 30000; // Increased timeout to 30 seconds

export async function GET(request: NextRequest) {
  console.log('🔍 ModelsLibrary API: Request received', {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries()),
    searchParams: Object.fromEntries(request.nextUrl.searchParams.entries())
  });

  try {
    // Forward the request to the backend models library endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const url = `${base}/api/models/library${queryString ? `?${queryString}` : ''}`;
    
    console.log('🔍 ModelsLibrary API: Backend URL constructed', {
      backendUrl: url,
      baseUrl: base,
      queryString: queryString
    });
    
    // Get Authorization header from the request
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
      console.log('🔍 ModelsLibrary API: Authorization header found', {
        hasAuth: true,
        authPrefix: authHeader.substring(0, 20) + '...'
      });
    } else {
      console.log('🔍 ModelsLibrary API: No authorization header');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => {
      console.log('🔍 ModelsLibrary API: Request timeout after', TIMEOUT_MS, 'ms');
      controller.abort();
    }, TIMEOUT_MS);
    
    try {
      console.log('🔍 ModelsLibrary API: Attempting backend fetch', { url, timeout: TIMEOUT_MS, backendUrl: BACKEND_URL });
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
        // Remove deprecated options that might cause issues
        cache: 'no-store',
      });
      
      clearTimeout(timeout);
      
      console.log('🔍 ModelsLibrary API: Backend response received', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        ok: response.ok,
        url: response.url
      });
      
      const contentType = response.headers.get('content-type') || '';
      let data: any = {};
      
      if (contentType.includes('application/json')) {
        try {
          data = await response.json();
          console.log('🔍 ModelsLibrary API: JSON response parsed successfully', {
            dataKeys: Object.keys(data),
            hasModels: Array.isArray(data.models),
            modelsCount: Array.isArray(data.models) ? data.models.length : 'N/A',
            responseStructure: data
          });
        } catch (parseError) {
          console.error('🔍 ModelsLibrary API: JSON parse error', { error: parseError });
          data = { models: [] };
        }
      } else {
        try {
          const text = await response.text();
          console.log('🔍 ModelsLibrary API: Non-JSON response', {
            contentType: contentType,
            textPreview: text.substring(0, 200) + (text.length > 200 ? '...' : ''),
            textLength: text.length
          });
          data = { models: [], message: text };
        } catch (textError) {
          console.error('🔍 ModelsLibrary API: Text read error', { error: textError });
          data = { models: [] };
        }
      }

      console.log('🔍 ModelsLibrary API: Returning response to frontend', {
        status: response.status,
        dataStructure: data
      });

      return NextResponse.json(data, { status: response.status });
      
    } catch (err: any) {
      clearTimeout(timeout);
      console.error('🔍 ModelsLibrary API: Backend fetch error', {
        error: err.message,
        errorType: err.name,
        stack: err.stack
      });
      
      // Return a fallback response with some default models
      const fallbackResponse = {
        models: [
          {
            id: 'local:tinyllama-1.1b',
            name: 'TinyLlama 1.1B',
            type: 'local',
            status: 'available',
            description: 'Local TinyLlama model for development'
          }
        ],
        total: 1,
        status: 'fallback'
      };
      
      console.log('🔍 ModelsLibrary API: Returning fallback response', fallbackResponse);
      return NextResponse.json(fallbackResponse, { status: 200 });
    }
    
  } catch (error) {
    console.error('🔍 ModelsLibrary API: Proxy error', error);
    const fallbackResponse = {
      models: [
        {
          id: 'local:tinyllama-1.1b',
          name: 'TinyLlama 1.1B',
          type: 'local',
          status: 'available',
          description: 'Local TinyLlama model for development'
        }
      ],
      total: 1,
      status: 'fallback'
    };
    
    console.log('🔍 ModelsLibrary API: Returning error fallback', fallbackResponse);
    return NextResponse.json(fallbackResponse, { status: 200 });
  }
}