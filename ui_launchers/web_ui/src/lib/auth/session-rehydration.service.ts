import { TokenValidationService, TokenExpiredError, TokenValidationError } from './token-validation.service';
import { setSession, clearSession, SessionData } from './session';

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
    this.rehydratePromise = this.performRehydration();
    try {
      await this.rehydratePromise;
    } finally {
      this.rehydratePromise = null;
    }
  }

  private async performRehydration(): Promise<void> {
    try {
      const result = await this.validator.validateToken();
      if (result.valid && result.user) {
        const session: SessionData = {
          accessToken: 'validated',
          expiresAt: Date.now() + 15 * 60 * 1000,
          userId: result.user.user_id,
          email: result.user.email,
          roles: result.user.roles,
          tenantId: result.user.tenant_id,
        };
        setSession(session);
        this.state = 'authenticated';
        return;
      }

      this.state = 'unauthenticated';
      clearSession();
    } catch (err) {
      if (err instanceof TokenExpiredError) {
        this.state = 'unauthenticated';
      } else if (err instanceof TokenValidationError) {
        this.state = 'error';
      } else {
        this.state = 'error';
      }
      clearSession();
      throw err;
    }
  }
}
