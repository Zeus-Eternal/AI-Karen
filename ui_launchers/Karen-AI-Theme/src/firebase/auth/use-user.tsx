
'use client';

/**
 * Mock user hook. Since backend logic is removed, this returns a static, non-authenticated state.
 * This prevents UI components that use this hook from breaking.
 */
export function useUser() {
  return { user: null, loading: false };
}
