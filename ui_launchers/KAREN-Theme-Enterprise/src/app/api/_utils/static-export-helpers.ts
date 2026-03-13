import { NextRequest } from 'next/server';

/**
 * Helper function to safely get search parameters from a request
 * Returns an empty URLSearchParams if request.url is not available (static export)
 */
export function safeGetSearchParams(request: NextRequest): URLSearchParams {
  try {
    // During static export, request.url might not be available
    if (!request.url) {
      return new URLSearchParams();
    }
    return new URL(request.url).searchParams;
  } catch {
    return new URLSearchParams();
  }
}

/**
 * Helper function to safely get headers from a request
 * Returns an empty Headers object if headers are not available (static export)
 */
export function safeGetHeaders(request: NextRequest): Headers {
  try {
    // During static export, request.headers might not be available
    if (!request.headers) {
      return new Headers();
    }
    return request.headers;
  } catch {
    return new Headers();
  }
}

/**
 * Helper function to safely get nextUrl from a request
 * Returns a dummy URL object if nextUrl is not available (static export)
 */
export function safeGetNextUrl(request: NextRequest): URL {
  try {
    // During static export, request.nextUrl might not be available
    if (!request.nextUrl) {
      // Use environment variable if available, otherwise fallback to localhost
      const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
      return new URL(baseUrl);
    }
    return request.nextUrl;
  } catch {
    // Use environment variable if available, otherwise fallback to localhost
    const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
    return new URL(baseUrl);
  }
}
