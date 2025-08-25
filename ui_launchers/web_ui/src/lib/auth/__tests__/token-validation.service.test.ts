import { describe, it, expect, vi } from 'vitest';

vi.mock('@/lib/api-client', () => ({
  getApiClient: vi.fn(),
}));

import {
  TokenValidationService,
  TokenExpiredError,
  TokenNetworkError,
} from '../token-validation.service';
import { getApiClient } from '@/lib/api-client';

describe('TokenValidationService', () => {
  it('validates token successfully', async () => {
    const getMock = vi.fn().mockResolvedValue({
      data: {
        valid: true,
        user: { user_id: '1', email: 'a@b.com', roles: ['user'], tenant_id: 't1' },
      },
    });
    (getApiClient as unknown as vi.Mock).mockReturnValue({ get: getMock });
    const service = new TokenValidationService();
    const result = await service.validateToken();
    expect(result.valid).toBe(true);
    expect(getMock).toHaveBeenCalledTimes(1);
  });

  it('throws TokenExpiredError when token expired', async () => {
    const getMock = vi.fn().mockResolvedValue({ data: { valid: false, expired: true } });
    (getApiClient as unknown as vi.Mock).mockReturnValue({ get: getMock });
    const service = new TokenValidationService();
    await expect(service.validateToken()).rejects.toBeInstanceOf(TokenExpiredError);
  });

  it('retries network errors and throws TokenNetworkError', async () => {
    const getMock = vi.fn().mockRejectedValue({});
    (getApiClient as unknown as vi.Mock).mockReturnValue({ get: getMock });
    const service = new TokenValidationService(2, 1);
    await expect(service.validateToken()).rejects.toBeInstanceOf(TokenNetworkError);
    expect(getMock).toHaveBeenCalledTimes(3);
  });
});
