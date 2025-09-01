import {
  TokenValidationService,
  TokenExpiredError,
  TokenValidationError,
  TokenNetworkError,
} from './token-validation.service';
import { setSession, clearSession, type SessionData } from './session';
import { authStateManager } from '@/contexts/AuthStateManager';
import type { SessionUser } from '@/contexts/SessionProvider';

export type RehydrationState = 'idle' | 'rehydrating' | 'authenticated' | 'unauthenticated' | 'error';

export class SessionRehydrationService {
  private state: RehydrationState = 'idle';
  private rehydratePromise: Promise<void> | null = null;

  constructor(private validator = new TokenValidationService()) {}

  get currentState(): RehydrationState {
    return this.state;
  }

  async rehydrate(): Promise<void> {
    if (this.rehydratePromise) {
      return this.rehydratePromise;
    }

    this.state = 'rehydrating';
    this.rehydratePromise = this.performWithRetry();
    try {
      await this.rehydratePromise;
    } finally {
      this.rehydratePromise = null;
    }
  }

  private async performWithRetry(retries = 3, baseDelay = 200): Promise<void> {
    let attempt = 0;
    while (attempt < retries) {
      try {
        await this.performRehydration();
        return;
      } catch (err) {
        if (err instanceof TokenNetworkError) {
          if (attempt === retries - 1) {
            throw err;
          }
          const delay = baseDelay * Math.pow(2, attempt);
          await new Promise(res => setTimeout(res, delay));
          attempt += 1;
          continue;
        }
        throw err;
      }
    }
  }

  private async performRehydration(): Promise<void> {
    try {
      const result = await this.validator.validateToken();
      if (result.valid && result.session) {
        setSession(result.session);
        // Propagate auth state so AuthContext/ProtectedRoute see the change
        const s = result.session;
        const sessionUser: SessionUser = {
          userId: s.userId,
          email: s.email,
          roles: s.roles,
          tenantId: s.tenantId,
        };
        authStateManager.updateState({ isAuthenticated: true, user: sessionUser });
        this.state = 'authenticated';
        return;
      }

      this.state = 'unauthenticated';
      clearSession();
      authStateManager.updateState({ isAuthenticated: false, user: null });
    } catch (err) {
      if (err instanceof TokenExpiredError) {
        this.state = 'unauthenticated';
      } else if (err instanceof TokenValidationError) {
        this.state = 'error';
      } else if (err instanceof TokenNetworkError) {
        this.state = 'error';
      } else {
        this.state = 'error';
      }
      clearSession();
      authStateManager.updateState({ isAuthenticated: false, user: null });
      throw err;
    }
  }
}
