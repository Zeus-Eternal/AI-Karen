import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

// JWT Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '1h';

// Test user credentials (as specified in the plan)
const TEST_USER_CREDENTIALS = {
  email: 'testuser@example.com',
  password: 'testpassword123', // This will be hashed
  userId: 'test-user-123',
  roles: ['user'],
  profile: {
    firstName: 'Test',
    lastName: 'User'
  }
};

// Hash the test password
const TEST_PASSWORD_HASH = bcrypt.hashSync(TEST_USER_CREDENTIALS.password, 10);

export interface JWTPayload {
  userId: string;
  email: string;
  roles: string[];
  iat?: number;
  exp?: number;
}

export interface TokenResponse {
  success: boolean;
  token?: string;
  user?: {
    userId: string;
    email: string;
    roles: string[];
    profile?: {
      firstName?: string;
      lastName?: string;
    };
  };
  error?: string;
}

/**
 * Generate a JWT token for a user
 */
export function generateToken(payload: Omit<JWTPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN } as jwt.SignOptions);
}

/**
 * Verify and decode a JWT token
 */
export function verifyToken(token: string): JWTPayload | null {
  try {
    const decoded = jwt.verify(token, JWT_SECRET) as JWTPayload;
    return decoded;
  } catch (error) {
    console.error('JWT verification failed:', error);
    return null;
  }
}

/**
 * Authenticate user credentials and return token
 */
export function authenticateUser(email: string, password: string): TokenResponse {
  try {
    // Check if credentials match test user
    if (email === TEST_USER_CREDENTIALS.email) {
      // Verify password
      const isPasswordValid = bcrypt.compareSync(password, TEST_PASSWORD_HASH);

      if (isPasswordValid) {
        const payload: Omit<JWTPayload, 'iat' | 'exp'> = {
          userId: TEST_USER_CREDENTIALS.userId,
          email: TEST_USER_CREDENTIALS.email,
          roles: TEST_USER_CREDENTIALS.roles
        };

        const token = generateToken(payload);

        return {
          success: true,
          token,
          user: {
            userId: TEST_USER_CREDENTIALS.userId,
            email: TEST_USER_CREDENTIALS.email,
            roles: TEST_USER_CREDENTIALS.roles,
            profile: TEST_USER_CREDENTIALS.profile
          }
        };
      }
    }

    return {
      success: false,
      error: 'Invalid email or password'
    };
  } catch (error) {
    console.error('Authentication error:', error);
    return {
      success: false,
      error: 'Authentication failed'
    };
  }
}

/**
 * Extract token from Authorization header or cookies
 */
export function extractToken(request: Request): string | null {
  // Try to get from Authorization header first
  const authHeader = request.headers.get('authorization');
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  // Try to get from cookies (for client-side requests)
  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) {
    const cookies = cookieHeader.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=');
      if (key && value) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, string>);

    return cookies.token || null;
  }

  return null;
}

/**
 * Middleware function to verify JWT token
 */
export function requireAuth(handler: (request: Request, context: unknown, user: JWTPayload) => Promise<Response>) {
  return async (request: Request, context: unknown): Promise<Response> => {
    const token = extractToken(request);

    if (!token) {
      return Response.json(
        { success: false, error: 'Authentication required' },
        { status: 401 }
      );
    }

    const user = verifyToken(token);

    if (!user) {
      return Response.json(
        { success: false, error: 'Invalid or expired token' },
        { status: 401 }
      );
    }

    return handler(request, context, user);
  };
}

/**
 * Set secure HTTP-only cookie with JWT token
 */
export function setAuthCookie(response: Response, token: string): void {
  const cookieValue = `token=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${3600}`; // 1 hour

  // Note: In Next.js API routes, we'll set this differently
  // This is a utility function for reference
  console.log('Setting auth cookie:', cookieValue);
}

/**
 * Clear auth cookie
 */
export function clearAuthCookie(): string {
  return 'token=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0';
}
