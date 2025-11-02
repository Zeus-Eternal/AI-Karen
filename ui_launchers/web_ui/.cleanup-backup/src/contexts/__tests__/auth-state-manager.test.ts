import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authStateManager, type AuthSnapshot } from '@/contexts/AuthStateManager';

// Mock sessionStorage
beforeEach(() => {
  vi.stubGlobal('sessionStorage', {
    getItem: vi.fn().mockReturnValue(null),
    setItem: vi.fn(),
  });
});

describe('AuthStateManager', () => {
  it('should update and persist state', () => {
    const snapshot: AuthSnapshot = { isAuthenticated: true, user: { userId: '1', email: 'test', roles: [], tenantId: 't' } };
    authStateManager.updateState(snapshot);
    expect(authStateManager.getState()).toEqual(snapshot);
    expect(sessionStorage.setItem).toHaveBeenCalled();
  });

  it('should notify subscribers on state change', () => {
    const listener = vi.fn();
    const unsubscribe = authStateManager.subscribe(listener);
    const snapshot: AuthSnapshot = { isAuthenticated: false, user: null };
    authStateManager.updateState(snapshot);
    expect(listener).toHaveBeenCalledWith(snapshot);
    unsubscribe();
  });
});
