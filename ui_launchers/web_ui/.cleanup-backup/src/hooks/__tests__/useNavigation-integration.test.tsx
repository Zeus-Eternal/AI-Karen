import { describe, it, expect } from 'vitest';
import { useNavigation } from '../useNavigation';

describe('useNavigation Hook Integration', () => {
  it('exports useNavigation hook correctly', () => {
    expect(useNavigation).toBeDefined();
    expect(typeof useNavigation).toBe('function');
  });
});