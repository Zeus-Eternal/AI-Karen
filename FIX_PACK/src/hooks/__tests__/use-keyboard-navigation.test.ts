import { renderHook, act } from '@testing-library/react';
import { useKeyboardNavigation, createChatKeyboardShortcuts } from '../use-keyboard-navigation';

// Mock telemetry hook
jest.mock('../use-telemetry', () => ({
  useTelemetry: () => ({
    track: jest.fn()
  })
}));

describe('useKeyboardNavigation', () => {
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
  });

  it('should initialize with default options', () => {
    const { result } = renderHook(() => useKeyboardNavigation());
    
    expect(result.current.containerRef).toBeDefined();
    expect(result.current.focusFirst).toBeInstanceOf(Function);
    expect(result.current.focusLast).toBeInstanceOf(Function);
    expect(result.current.focusNext).toBeInstanceOf(Function);
    expect(result.current.focusPrevious).toBeInstanceOf(Function);
  });

  it('should find focusable elements', () => {
    container.innerHTML = `
      <button>Button 1</button>
      <input type="text" />
      <button disabled>Disabled Button</button>
      <a href="#">Link</a>
      <div tabindex="0">Focusable Div</div>
      <div tabindex="-1">Non-focusable Div</div>
    `;

    const { result } = renderHook(() => useKeyboardNavigation());
    
    act(() => {
      result.current.containerRef.current = container;
    });

    const focusableElements = result.current.getFocusableElements();
    expect(focusableElements).toHaveLength(4); // button, input, link, focusable div
  });

  it('should handle focus navigation', () => {
    container.innerHTML = `
      <button id="btn1">Button 1</button>
      <button id="btn2">Button 2</button>
      <button id="btn3">Button 3</button>
    `;

    const { result } = renderHook(() => useKeyboardNavigation());
    
    act(() => {
      result.current.containerRef.current = container;
    });

    // Focus first element
    act(() => {
      result.current.focusFirst();
    });
    expect(document.activeElement?.id).toBe('btn1');

    // Focus next element
    act(() => {
      result.current.focusNext();
    });
    expect(document.activeElement?.id).toBe('btn2');

    // Focus last element
    act(() => {
      result.current.focusLast();
    });
    expect(document.activeElement?.id).toBe('btn3');

    // Focus previous element
    act(() => {
      result.current.focusPrevious();
    });
    expect(document.activeElement?.id).toBe('btn2');
  });

  it('should handle keyboard shortcuts', () => {
    const mockAction = jest.fn();
    const shortcuts = [
      {
        key: 'k',
        ctrlKey: true,
        action: mockAction,
        description: 'Test shortcut'
      }
    ];

    const { result } = renderHook(() => 
      useKeyboardNavigation({ shortcuts })
    );

    act(() => {
      result.current.containerRef.current = container;
    });

    // Simulate Ctrl+K
    const event = new KeyboardEvent('keydown', {
      key: 'k',
      ctrlKey: true,
      bubbles: true
    });

    act(() => {
      container.dispatchEvent(event);
    });

    expect(mockAction).toHaveBeenCalled();
  });

  it('should handle escape key', () => {
    const mockEscape = jest.fn();
    
    const { result } = renderHook(() => 
      useKeyboardNavigation({ onEscape: mockEscape })
    );

    act(() => {
      result.current.containerRef.current = container;
    });

    const event = new KeyboardEvent('keydown', {
      key: 'Escape',
      bubbles: true
    });

    act(() => {
      container.dispatchEvent(event);
    });

    expect(mockEscape).toHaveBeenCalled();
  });

  it('should handle enter key', () => {
    const mockEnter = jest.fn();
    
    const { result } = renderHook(() => 
      useKeyboardNavigation({ onEnter: mockEnter })
    );

    act(() => {
      result.current.containerRef.current = container;
    });

    const event = new KeyboardEvent('keydown', {
      key: 'Enter',
      bubbles: true
    });

    act(() => {
      container.dispatchEvent(event);
    });

    expect(mockEnter).toHaveBeenCalled();
  });

  it('should trap focus when enabled', () => {
    container.innerHTML = `
      <button id="btn1">Button 1</button>
      <button id="btn2">Button 2</button>
    `;

    const { result } = renderHook(() => 
      useKeyboardNavigation({ trapFocus: true })
    );

    act(() => {
      result.current.containerRef.current = container;
      result.current.focusFirst();
    });

    expect(document.activeElement?.id).toBe('btn1');

    // Tab should move to next element
    const tabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true
    });

    act(() => {
      container.dispatchEvent(tabEvent);
    });

    expect(document.activeElement?.id).toBe('btn2');

    // Tab from last element should wrap to first
    act(() => {
      container.dispatchEvent(tabEvent);
    });

    expect(document.activeElement?.id).toBe('btn1');
  });

  it('should handle shift+tab for backward navigation', () => {
    container.innerHTML = `
      <button id="btn1">Button 1</button>
      <button id="btn2">Button 2</button>
    `;

    const { result } = renderHook(() => 
      useKeyboardNavigation({ trapFocus: true })
    );

    act(() => {
      result.current.containerRef.current = container;
      result.current.focusLast();
    });

    expect(document.activeElement?.id).toBe('btn2');

    // Shift+Tab should move to previous element
    const shiftTabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true
    });

    act(() => {
      container.dispatchEvent(shiftTabEvent);
    });

    expect(document.activeElement?.id).toBe('btn1');
  });
});

describe('createChatKeyboardShortcuts', () => {
  it('should create chat keyboard shortcuts', () => {
    const actions = {
      onSend: jest.fn(),
      onClear: jest.fn(),
      onAbort: jest.fn(),
      onFocusInput: jest.fn(),
      onToggleVoice: jest.fn(),
      onScrollToTop: jest.fn(),
      onScrollToBottom: jest.fn()
    };

    const shortcuts = createChatKeyboardShortcuts(actions);

    expect(shortcuts).toHaveLength(7);
    expect(shortcuts[0].key).toBe('Enter');
    expect(shortcuts[1].key).toBe('Escape');
    expect(shortcuts[2].key).toBe('k');
    expect(shortcuts[2].ctrlKey).toBe(true);
  });

  it('should handle missing actions gracefully', () => {
    const shortcuts = createChatKeyboardShortcuts({});
    
    expect(shortcuts).toHaveLength(7);
    expect(() => shortcuts[0].action()).not.toThrow();
  });
});