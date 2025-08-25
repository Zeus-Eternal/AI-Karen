import { getApiClient } from '@/lib/api-client';

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
  user?: {
    user_id: string;
    email: string;
    roles: string[];
    tenant_id: string;
  };
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
        const data = response.data as { valid: boolean; expired?: boolean; user?: ValidationResult['user'] };

        if (data.valid) {
          return { valid: true, user: data.user };
        }

        if (data.expired) {
          throw new TokenExpiredError();
        }

        throw new TokenValidationError('Invalid token');
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
