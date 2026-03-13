import { NextRequest, NextResponse } from 'next/server';
import { verifyToken, extractToken } from '@/lib/jwt';
import { type UserDataResponse, isValidUserDataResponse } from '@/types/auth';
import { z } from 'zod';
import { v4 as uuidv4 } from 'uuid';

// Schema for user data submission
const userDataSchema = z.object({
  // Add any specific fields you expect in the user data submission
  // For now, we'll accept any additional data
  data: z.any().optional(),
});

export async function POST(request: NextRequest): Promise<NextResponse<UserDataResponse>> {
  try {
    // Extract and verify token
    const token = extractToken(request);
    
    if (!token) {
      return NextResponse.json(
        {
          error: 'Authentication required'
        } as any,
        { status: 401 }
      );
    }

    const payload = verifyToken(token);
    
    if (!payload) {
      return NextResponse.json(
        {
          error: 'Invalid or expired token'
        } as any,
        { status: 401 }
      );
    }

    // Parse request body
    let body;
    try {
      body = await request.json();
    } catch (error) {
      return NextResponse.json(
        {
          error: 'Invalid request body',
          userId: '',
          submissionId: '',
          submissionTimestamp: new Date().toISOString()
        } as UserDataResponse,
        { status: 400 }
      );
    }

    // Validate input (optional for this endpoint)
    const validationResult = userDataSchema.safeParse(body);
    if (!validationResult.success) {
      const errorMessage = validationResult.error.errors.map(err => err.message).join(', ');
      return NextResponse.json(
        {
          error: errorMessage,
          userId: '',
          submissionId: '',
          submissionTimestamp: new Date().toISOString()
        } as UserDataResponse,
        { status: 400 }
      );
    }

    // Generate response data as specified in the plan
    const responseData: UserDataResponse = {
      userId: payload.userId,
      submissionId: uuidv4(),
      submissionTimestamp: new Date().toISOString(),
    };

    // Validate response data
    if (!isValidUserDataResponse(responseData)) {
      console.error('Generated invalid response data:', responseData);
      return NextResponse.json(
        {
          error: 'Internal server error',
          userId: '',
          submissionId: '',
          submissionTimestamp: new Date().toISOString()
        } as UserDataResponse,
        { status: 500 }
      );
    }

    // Add CORS headers for development
    const response = NextResponse.json(responseData, { status: 200 });
    
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
    console.error('User data API error:', error);
    
    return NextResponse.json(
      {
        error: 'Internal server error',
        userId: '',
        submissionId: '',
        submissionTimestamp: new Date().toISOString()
      } as UserDataResponse,
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