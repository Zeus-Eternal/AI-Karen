import { describe, it, expect, vi } from 'vitest';
import { SessionRehydrationService } from '../session-rehydration.service';
import { TokenExpiredError } from '../token-validation.service';
import * as sessionModule from '../session';

describe('SessionRehydrationService', () => {
  it('rehydrates and sets session on success', async () => {
    const validator = { validateToken: vi.fn().mockResolvedValue({ valid: true, user: { user_id: '1', email: 'a', roles: [], tenant_id: 't1' } }) };
    const setSpy = vi.spyOn(sessionModule, 'setSession').mockImplementation(() => {});
    const service = new SessionRehydrationService(validator as any);

    await service.rehydrate();

    expect(setSpy).toHaveBeenCalled();
    expect(service.currentState).toBe('authenticated');
  });

  it('clears session and throws on expired token', async () => {
    const validator = { validateToken: vi.fn().mockRejectedValue(new TokenExpiredError()) };
    const clearSpy = vi.spyOn(sessionModule, 'clearSession').mockImplementation(() => {});
    const service = new SessionRehydrationService(validator as any);

    await expect(service.rehydrate()).rejects.toBeInstanceOf(TokenExpiredError);
    expect(clearSpy).toHaveBeenCalled();
    expect(service.currentState).toBe('unauthenticated');
  });
});
