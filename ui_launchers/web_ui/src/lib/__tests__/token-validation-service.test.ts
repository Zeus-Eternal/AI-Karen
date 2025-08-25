import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TokenValidationService, TokenExpiredError, TokenNetworkError } from '@/lib/auth/token-validation.service';

const api = { get: vi.fn(), post: vi.fn() };
vi.mock('@/lib/api-client', () => ({
  getApiClient: () => api,
}));

beforeEach(() => {
  vi.resetAllMocks();
});

describe('TokenValidationService', () => {
  it('returns session when token valid', async () => {
    api.get.mockResolvedValue({ data: { valid: true, user: { user_id: '1', email: 'e', roles: [], tenant_id: 't' } } });
    const svc = new TokenValidationService();
    const result = await svc.validateToken();
    expect(result.valid).toBe(true);
    expect(result.session?.userId).toBe('1');
  });
  it('returns invalid result when token is invalid', async () => {
    api.get.mockResolvedValue({ data: { valid: false } });
    const svc = new TokenValidationService();
    const result = await svc.validateToken();
    expect(result.valid).toBe(false);
    expect(result.session).toBeUndefined();
  });
  it('refreshes when token expired', async () => {
    api.get.mockResolvedValueOnce({ data: { valid: false, expired: true } });
    api.post.mockResolvedValueOnce({ data: { access_token: 'a', expires_in: 1, user_data: { user_id: '1', email: 'e', roles: [], tenant_id: 't' } } });
    const svc = new TokenValidationService();
    const result = await svc.validateToken();
    expect(api.post).toHaveBeenCalled();
    expect(result.session?.accessToken).toBe('a');
  });

  it('throws TokenExpiredError when refresh fails', async () => {
    api.get.mockResolvedValueOnce({ data: { valid: false, expired: true } });
    api.post.mockRejectedValueOnce(new Error('fail'));
    const svc = new TokenValidationService();
    await expect(svc.validateToken()).rejects.toBeInstanceOf(TokenExpiredError);
  });

  it('retries network errors and eventually throws', async () => {
    api.get.mockRejectedValue(new Error('network'));
    const svc = new TokenValidationService(1, 1);
    await expect(svc.validateToken()).rejects.toBeInstanceOf(TokenNetworkError);
  });
});
