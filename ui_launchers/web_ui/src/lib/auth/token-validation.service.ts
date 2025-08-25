import { getApiClient } from '@/lib/api-client';
import { type SessionData } from '@/lib/auth/session';

/**
 * Error thrown when token validation fails.
 */
export class TokenValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TokenValidationError';
  }
}

/**
 * Error thrown when token has expired.
 */
export class TokenExpiredError extends TokenValidationError {
  constructor() {
    super('Token expired');
    this.name = 'TokenExpiredError';
  }
}

/**
 * Error thrown when network requests fail after retries.
 */
export class TokenNetworkError extends TokenValidationError {
  constructor(message: string) {
    super(message);
    this.name = 'TokenNetworkError';
  }
}

interface ValidationResult {
  valid: boolean;
  session?: SessionData;
}

/**
 * Service responsible for validating authentication tokens with retry logic.
 * Handles token expiration detection and propagates meaningful errors.
 */
export class TokenValidationService {
  constructor(private maxRetries = 3, private baseDelayMs = 200) {}

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async validateToken(): Promise<ValidationResult> {
    const api = getApiClient();
    let attempt = 0;

    while (attempt <= this.maxRetries) {
      try {
        const response = await api.get('/api/auth/validate-session');
        const data = response.data as {
          valid: boolean;
          expired?: boolean;
          user?: {
            user_id: string;
            email: string;
            roles: string[];
            tenant_id: string;
          };
        };

        if (data.valid && data.user) {
          const session: SessionData = {
            accessToken: 'validated',
            expiresAt: Date.now() + 15 * 60 * 1000,
            userId: data.user.user_id,
            email: data.user.email,
            roles: data.user.roles,
            tenantId: data.user.tenant_id,
          };
          return { valid: true, session };
        }

        if (data.expired) {
          try {
            const refresh = await api.post('/api/auth/refresh');
            const refreshData = refresh.data as {
              access_token: string;
              expires_in: number;
              user_data: {
                user_id: string;
                email: string;
                roles: string[];
                tenant_id: string;
              };
            };

            const session: SessionData = {
              accessToken: refreshData.access_token,
              expiresAt: Date.now() + refreshData.expires_in * 1000,
              userId: refreshData.user_data.user_id,
              email: refreshData.user_data.email,
              roles: refreshData.user_data.roles,
              tenantId: refreshData.user_data.tenant_id,
            };
            return { valid: true, session };
          } catch {
            throw new TokenExpiredError();
          }
        }

        // For invalid tokens, treat as unauthenticated without throwing an error
        return { valid: false };
      } catch (err: any) {
        if (err instanceof TokenValidationError) {
          throw err;
        }

        const isNetwork = !err.response;

        if (!isNetwork) {
          throw new TokenValidationError(err.message || 'Token validation failed');
        }

        if (attempt === this.maxRetries) {
          throw new TokenNetworkError('Network error during token validation');
        }

        const delay = this.baseDelayMs * Math.pow(2, attempt);
        attempt += 1;
        await this.delay(delay);
      }
    }

    throw new TokenNetworkError('Token validation failed after retries');
  }
}
