import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { SessionRehydrationService } from '@/lib/auth/session-rehydration.service';
import { TokenValidationService } from '@/lib/auth/token-validation.service';
import { setSession, clearSession } from '@/lib/auth/session';

vi.mock('@/lib/auth/session', () => ({
  setSession: vi.fn(),
  clearSession: vi.fn(),
}));

describe('SessionRehydrationService', () => {
  const setSessionMock = setSession as unknown as Mock;
  const clearSessionMock = clearSession as unknown as Mock;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sets authenticated state when token valid', async () => {
    const validator = {
      validateToken: vi.fn().mockResolvedValue({ valid: true, session: { accessToken: 'a', expiresAt: 1, userId: 'u', email: 'e', roles: [], tenantId: 't' } })
    } as unknown as TokenValidationService;
    const svc = new SessionRehydrationService(validator);
    await svc.rehydrate();
    expect(setSessionMock).toHaveBeenCalled();
    expect(svc.currentState).toBe('authenticated');
  });

  it('clears session and sets unauthenticated when token invalid', async () => {
    const validator = {
      validateToken: vi.fn().mockResolvedValue({ valid: false })
    } as unknown as TokenValidationService;
    const svc = new SessionRehydrationService(validator);
    await svc.rehydrate();
    expect(clearSessionMock).toHaveBeenCalled();
    expect(svc.currentState).toBe('unauthenticated');
  });
});
