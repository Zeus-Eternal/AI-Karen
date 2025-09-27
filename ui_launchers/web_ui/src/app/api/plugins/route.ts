import { NextRequest, NextResponse } from 'next/server';

import { withBackendPath } from '@/app/api/_utils/backend';

export async function GET(request: NextRequest) {
  // Default response for build time or when backend is unavailable
  const defaultResponse = {
    plugins: [],
    total_count: 0,
    enabled_count: 0,
    disabled_count: 0,
  };

  try {
    // Skip fetch during build time (when NODE_ENV is not set or when building)
    if (process.env.NODE_ENV === undefined || process.env.NEXT_PHASE === 'phase-production-build') {
      return NextResponse.json(defaultResponse);
    }

    // Call the backend /plugins endpoint with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const response = await fetch(withBackendPath('/plugins'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    
    // Transform the response to match the expected format
    // Backend returns: { enabled: [], available: [], count: 0 }
    // Frontend expects: { plugins: [] }
    const transformedData = {
      plugins: [...(data.enabled || []), ...(data.available || [])],
      total_count: data.count || 0,
      enabled_count: (data.enabled || []).length,
      disabled_count: (data.available || []).length,
    };

    return NextResponse.json(transformedData);
  } catch (error) {
    console.error('Failed to fetch plugins:', error);
    
    // Return empty plugins list on error
    return NextResponse.json(defaultResponse);
  }
}