import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useExtensions } from '../useExtensions';

global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ extensions: [] }),
  })
) as any;

describe('useExtensions', () => {
  it('fetches extensions on mount', async () => {
    const { result } = renderHook(() => useExtensions());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalled();
    expect(result.current.extensions).toEqual([]);
  });
});
