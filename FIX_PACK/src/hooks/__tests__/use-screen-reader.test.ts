import { renderHook, act } from '@testing-library/react';
import { useScreenReader, createAriaLabel, createAriaDescribedBy, chatAriaPatterns } from '../use-screen-reader';

// Mock telemetry hook
jest.mock('../use-telemetry', () => ({
  useTelemetry: () => ({
    track: jest.fn()
  })
}));

describe('useScreenReader', () => {
  beforeEach(() => {
    // Clean up any existing live regions
    const existingRegions = document.querySelectorAll('[id^="live-region"]');
    existingRegions.forEach(region => region.remove());
  });

  afterEach(() => {
    // Clean up after each test
    const existingRegions = document.querySelectorAll('[id^="live-region"]');
    existingRegions.forEach(region => region.remove());
  });

  it('should create live regions on mount', () => {
    renderHook(() => useScreenReader());
    
    const liveRegion = document.getElementById('live-region-announcements');
    const statusRegion = document.getElementById('live-region-status');
    
    expect(liveRegion).toBeInTheDocument();
    expect(statusRegion).toBeInTheDocument();
    expect(liveRegion?.getAttribute('aria-live')).toBe('polite');
    expect(statusRegion?.getAttribute('role')).toBe('status');
  });

  it('should configure live region with custom options', () => {
    renderHook(() => useScreenReader({
      politeness: 'assertive',
      atomic: true,
      relevant: 'all'
    }));
    
    const liveRegion = document.getElementById('live-region-announcements');
    
    expect(liveRegion?.getAttribute('aria-live')).toBe('assertive');
    expect(liveRegion?.getAttribute('aria-atomic')).toBe('true');
    expect(liveRegion?.getAttribute('aria-relevant')).toBe('all');
  });

  it('should announce messages', async () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.announce('Test announcement');
    });

    // Wait for the timeout
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 20));
    });

    const liveRegion = document.getElementById('live-region-announcements');
    expect(liveRegion?.textContent).toBe('Test announcement');
  });

  it('should announce with different priorities', async () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.announce('Urgent message', 'assertive');
    });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 20));
    });

    const liveRegion = document.getElementById('live-region-announcements');
    expect(liveRegion?.getAttribute('aria-live')).toBe('assertive');
    expect(liveRegion?.textContent).toBe('Urgent message');
  });

  it('should announce with delay', async () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.announceWithDelay('Delayed message', 50);
    });

    // Message should not be there immediately
    const liveRegion = document.getElementById('live-region-announcements');
    expect(liveRegion?.textContent).toBe('');

    // Wait for delay
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 70));
    });

    expect(liveRegion?.textContent).toBe('Delayed message');
  });

  it('should set status messages', () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.setStatus('Loading...');
    });

    const statusRegion = document.getElementById('live-region-status');
    expect(statusRegion?.textContent).toBe('Loading...');
  });

  it('should announce progress', () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.announceProgress(3, 10, 'Upload');
    });

    const statusRegion = document.getElementById('live-region-status');
    expect(statusRegion?.textContent).toBe('Upload: 3 of 10, 30 percent complete');
  });

  it('should clear announcements', async () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.announce('Test message');
      result.current.setStatus('Test status');
    });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 20));
    });

    act(() => {
      result.current.clear();
    });

    const liveRegion = document.getElementById('live-region-announcements');
    const statusRegion = document.getElementById('live-region-status');
    
    expect(liveRegion?.textContent).toBe('');
    expect(statusRegion?.textContent).toBe('');
  });

  it('should announce on mount when specified', async () => {
    renderHook(() => useScreenReader({
      announceOnMount: 'Component loaded'
    }));

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 150));
    });

    const liveRegion = document.getElementById('live-region-announcements');
    expect(liveRegion?.textContent).toBe('Component loaded');
  });

  it('should handle empty messages gracefully', async () => {
    const { result } = renderHook(() => useScreenReader());
    
    act(() => {
      result.current.announce('');
      result.current.announce('   ');
    });

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 20));
    });

    const liveRegion = document.getElementById('live-region-announcements');
    expect(liveRegion?.textContent).toBe('');
  });
});

describe('createAriaLabel', () => {
  it('should create basic aria label', () => {
    const label = createAriaLabel('Send message');
    expect(label).toBe('Send message');
  });

  it('should include state in aria label', () => {
    const label = createAriaLabel('Send message', { state: 'disabled' });
    expect(label).toBe('Send message, disabled');
  });

  it('should include position in aria label', () => {
    const label = createAriaLabel('Message', { 
      position: { current: 2, total: 5 } 
    });
    expect(label).toBe('Message, 2 of 5');
  });

  it('should include description in aria label', () => {
    const label = createAriaLabel('Message', { 
      description: 'from assistant' 
    });
    expect(label).toBe('Message, from assistant');
  });

  it('should combine all context elements', () => {
    const label = createAriaLabel('Message', {
      state: 'selected',
      position: { current: 1, total: 3 },
      description: 'contains code'
    });
    expect(label).toBe('Message, selected, 1 of 3, contains code');
  });
});

describe('createAriaDescribedBy', () => {
  it('should combine valid IDs', () => {
    const describedBy = createAriaDescribedBy('id1', 'id2', 'id3');
    expect(describedBy).toBe('id1 id2 id3');
  });

  it('should filter out null and undefined values', () => {
    const describedBy = createAriaDescribedBy('id1', null, 'id2', undefined, 'id3');
    expect(describedBy).toBe('id1 id2 id3');
  });

  it('should handle empty input', () => {
    const describedBy = createAriaDescribedBy();
    expect(describedBy).toBe('');
  });
});

describe('chatAriaPatterns', () => {
  it('should provide message list pattern', () => {
    const pattern = chatAriaPatterns.messageList;
    expect(pattern.role).toBe('log');
    expect(pattern['aria-live']).toBe('polite');
    expect(pattern['aria-label']).toBe('Conversation messages');
  });

  it('should provide message pattern with context', () => {
    const pattern = chatAriaPatterns.message('user', '10:30 AM', 0, 5);
    expect(pattern.role).toBe('article');
    expect(pattern['aria-label']).toContain('user message');
    expect(pattern['aria-label']).toContain('1 of 5');
    expect(pattern['aria-label']).toContain('10:30 AM');
  });

  it('should provide streaming message pattern', () => {
    const pattern = chatAriaPatterns.streamingMessage;
    expect(pattern['aria-live']).toBe('polite');
    expect(pattern['aria-atomic']).toBe('false');
    expect(pattern['aria-label']).toBe('Assistant is typing');
  });

  it('should provide composer pattern', () => {
    const pattern = chatAriaPatterns.composer;
    expect(pattern.role).toBe('region');
    expect(pattern['aria-label']).toBe('Message composer');
  });

  it('should provide quick actions pattern', () => {
    const pattern = chatAriaPatterns.quickActions;
    expect(pattern.role).toBe('toolbar');
    expect(pattern['aria-label']).toBe('Quick actions');
  });
});