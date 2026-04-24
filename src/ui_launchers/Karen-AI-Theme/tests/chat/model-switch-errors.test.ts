import { describe, expect, it } from 'vitest';

import { ApiError } from '@/lib/api';
import { formatModelSwitchError } from '@/lib/model-switch-errors';

describe('formatModelSwitchError', () => {
  it('returns a clear credential action when provider key is invalid/expired', () => {
    const error = new ApiError(
      400,
      "API key validation failed: Error code: 401 - {'error': {'code': '401', 'message': 'token expired or incorrect'}}",
    );
    const message = formatModelSwitchError(error, 'Z.ai');

    expect(message).toContain('Z.ai credential is invalid or expired');
    expect(message).toContain('switch to local fallback');
  });

  it('returns provider timeout guidance on validation timeout', () => {
    const error = new ApiError(400, 'provider validation timed out');
    const message = formatModelSwitchError(error, 'OpenAI Compatible');

    expect(message).toContain('validation timed out');
    expect(message).toContain('base URL/network reachability');
  });
});
