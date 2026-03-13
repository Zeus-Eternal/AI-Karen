import { NextRequest, NextResponse } from 'next/server';
import { authenticateUser, type TokenResponse } from '@/lib/jwt';
import { loginSchema, type AuthResponse } from '@/types/auth';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

// Rate limiting store (in production, use Redis or similar)
const loginAttempts = new Map<string, { count: number; lastAttempt: number }>();
const RATE_LIMIT_WINDOW = 15 * 60 * 1000; // 15 minutes in milliseconds
const MAX_ATTEMPTS = 5;

function getClientIdentifier(request: NextRequest): string {
  // Try to get client IP from various headers
  const forwarded = request.headers.get('x-forwarded-for');
  const realIp = request.headers.get('x-real-ip');
  const ip = forwarded?.split(',')[0] || realIp || 'unknown';
  return ip;
}

function isRateLimited(clientId: string): boolean {
  const now = Date.now();
  const attempts = loginAttempts.get(clientId);

  if (!attempts) {
    return false;
  }

  // Reset if window has passed
  if (now - attempts.lastAttempt > RATE_LIMIT_WINDOW) {
    loginAttempts.delete(clientId);
    return false;
  }

  return attempts.count >= MAX_ATTEMPTS;
}

function recordLoginAttempt(clientId: string): void {
  const now = Date.now();
  const attempts = loginAttempts.get(clientId) || { count: 0, lastAttempt: now };
  
  attempts.count++;
  attempts.lastAttempt = now;
  loginAttempts.set(clientId, attempts);
}

export async function POST(request: NextRequest): Promise<NextResponse<AuthResponse>> {
  try {
    // Get client identifier for rate limiting
    const clientId = getClientIdentifier(request);

    // Check rate limiting
    if (isRateLimited(clientId)) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Too many login attempts. Please try again later.' 
        },
        { 
          status: 429,
          headers: {
            'Retry-After': '900', // 15 minutes
          }
        }
      );
    }

    // Parse request body
    let body;
    try {
      body = await request.json();
    } catch (error) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Invalid request body' 
        },
        { status: 400 }
      );
    }

    // Validate input
    const validationResult = loginSchema.safeParse(body);
    if (!validationResult.success) {
      const errorMessage = validationResult.error.errors.map(err => err.message).join(', ');
      return NextResponse.json(
        { 
          success: false, 
          error: errorMessage 
        },
        { status: 400 }
      );
    }

    const { email, password } = validationResult.data;

    // Record login attempt for rate limiting
    recordLoginAttempt(clientId);

    // Authenticate user
    const authResult: TokenResponse = authenticateUser(email, password);

    if (!authResult.success) {
      return NextResponse.json(
        { 
          success: false, 
          error: authResult.error || 'Authentication failed' 
        },
        { status: 401 }
      );
    }

    // Clear successful login attempts
    loginAttempts.delete(clientId);

    // Set secure HTTP-only cookie with JWT token
    const response = NextResponse.json(
      {
        success: true,
        userId: authResult.user?.userId,
        user: authResult.user
      } as AuthResponse,
      { status: 200 }
    );

    // Set secure cookie
    if (authResult.token) {
      response.cookies.set('token', authResult.token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 3600, // 1 hour in seconds
        path: '/'
      });
    }

    // Add CORS headers for development
    if (process.env.NODE_ENV === 'development') {
      response.headers.set('Access-Control-Allow-Origin', '*');
      response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
      response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    }

    // Add security headers
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-XSS-Protection', '1; mode=block');

    return response;

  } catch (error) {
    console.error('Login API error:', error);
    
    return NextResponse.json(
      { 
        success: false, 
        error: 'Internal server error' 
      },
      { status: 500 }
    );
  }
}

// Handle OPTIONS requests for CORS preflight
export async function OPTIONS(request: NextRequest): Promise<NextResponse> {
  const response = new NextResponse(null, { status: 200 });
  
  if (process.env.NODE_ENV === 'development') {
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  }
  
  return response;
}