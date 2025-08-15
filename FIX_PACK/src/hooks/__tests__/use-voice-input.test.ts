# Path: ui_launchers/web_ui/src/hooks/__tests__/use-voice-input.test.ts

import { renderHook, act } from '@testing-library/react';
import { useVoiceInput } from '../use-voice-input';
import { useTelemetry } from '@/hooks/use-telemetry';

// Mock dependencies
jest.mock('@/hooks/use-telemetry');

const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;

// Mock SpeechRecognition
class MockSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = 'en-US';
  
  onresult: ((event: any) => void) | null = null;
  onstart: (() => void) | null = null;
  onend: (() => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onnomatch: (() => void) | null = null;

  start = jest.fn(() => {
    this.onstart?.();
  });

  stop = jest.fn(() => {
    this.onend?.();
  });

  abort = jest.fn(() => {
    this.onend?.();
  });

  // Helper methods for testing
  simulateResult(transcript: string, isFinal: boolean = true) {
    const event = {
      resultIndex: 0,
      results: [
        {
          0: { transcript },
          isFinal,
          length: 1
        }
      ]
    };
    this.onresult?.(event);
  }

  simulateError(error: string) {
    this.onerror?.({ error });
  }

  simulateNoMatch() {
    this.onnomatch?.();
  }
}

// Setup global mocks
const mockRecognition = new MockSpeechRecognition();
Object.defineProperty(global, 'SpeechRecognition', {
  value: jest.fn(() => mockRecognition),
  configurable: true
});

Object.defineProperty(global, 'webkitSpeechRecognition', {
  value: jest.fn(() => mockRecognition),
  configurable: true
});

describe('useVoiceInput', () => {
  const mockTrack = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    // Reset mock recognition
    mockRecognition.start.mockClear();
    mockRecognition.stop.mockClear();
    mockRecognition.abort.mockClear();
  });

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useVoiceInput());

    expect(result.current.isRecording).toBe(false);
    expect(result.current.isSupported).toBe(true);
    expect(result.current.transcript).toBe('');
    expect(result.current.interimTranscript).toBe('');
    expect(result.current.error).toBe(null);
  });

  it('should detect browser support', () => {
    const { result } = renderHook(() => useVoiceInput());

    expect(result.current.isSupported).toBe(true);
  });

  it('should handle unsupported browser', () => {
    // Temporarily remove SpeechRecognition
    const originalSpeechRecognition = global.SpeechRecognition;
    const originalWebkitSpeechRecognition = global.webkitSpeechRecognition;
    
    delete (global as any).SpeechRecognition;
    delete (global as any).webkitSpeechRecognition;

    const { result } = renderHook(() => useVoiceInput());

    expect(result.current.isSupported).toBe(false);

    // Restore
    global.SpeechRecognition = originalSpeechRecognition;
    global.webkitSpeechRecognition = originalWebkitSpeechRecognition;
  });

  it('should start recording successfully', () => {
    const onStart = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onStart }));

    act(() => {
      result.current.startRecording();
    });

    expect(mockRecognition.start).toHaveBeenCalled();
    expect(result.current.isRecording).toBe(true);
    expect(onStart).toHaveBeenCalled();
    expect(mockTrack).toHaveBeenCalledWith('voice_input_started', { language: 'en-US' });
  });

  it('should stop recording successfully', () => {
    const onEnd = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onEnd }));

    // Start recording first
    act(() => {
      result.current.startRecording();
    });

    // Then stop
    act(() => {
      result.current.stopRecording();
    });

    expect(mockRecognition.stop).toHaveBeenCalled();
    expect(result.current.isRecording).toBe(false);
    expect(onEnd).toHaveBeenCalled();
  });

  it('should handle transcript results', () => {
    const onTranscript = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onTranscript }));

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateResult('Hello world', true);
    });

    expect(result.current.transcript).toBe('Hello world');
    expect(onTranscript).toHaveBeenCalledWith('Hello world');
    expect(mockTrack).toHaveBeenCalledWith('voice_input_transcript', {
      transcriptLength: 11,
      language: 'en-US'
    });
  });

  it('should handle interim results', () => {
    const { result } = renderHook(() => useVoiceInput({ interimResults: true }));

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateResult('Hello', false);
    });

    expect(result.current.interimTranscript).toBe('Hello');
    expect(result.current.transcript).toBe('');
  });

  it('should accumulate multiple final results', () => {
    const onTranscript = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onTranscript }));

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateResult('Hello ', true);
    });

    act(() => {
      mockRecognition.simulateResult('world', true);
    });

    expect(result.current.transcript).toBe('Hello world');
    expect(onTranscript).toHaveBeenCalledTimes(2);
  });

  it('should handle recognition errors', () => {
    const onError = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onError }));

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateError('network');
    });

    expect(result.current.error).toBe('Speech recognition error: network');
    expect(result.current.isRecording).toBe(false);
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
    expect(mockTrack).toHaveBeenCalledWith('voice_input_error', {
      error: 'network',
      language: 'en-US'
    });
  });

  it('should handle no match', () => {
    const onError = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onError }));

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateNoMatch();
    });

    expect(result.current.error).toBe('No speech was detected');
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
  });

  it('should clear transcript', () => {
    const { result } = renderHook(() => useVoiceInput());

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateResult('Hello world', true);
    });

    expect(result.current.transcript).toBe('Hello world');

    act(() => {
      result.current.clearTranscript();
    });

    expect(result.current.transcript).toBe('');
    expect(result.current.interimTranscript).toBe('');
    expect(result.current.error).toBe(null);
  });

  it('should handle start recording when unsupported', () => {
    // Mock unsupported browser
    delete (global as any).SpeechRecognition;
    delete (global as any).webkitSpeechRecognition;

    const onError = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onError }));

    act(() => {
      result.current.startRecording();
    });

    expect(result.current.error).toBe('Speech recognition is not supported in this browser');
    expect(onError).toHaveBeenCalledWith(expect.any(Error));

    // Restore
    global.SpeechRecognition = jest.fn(() => mockRecognition);
    global.webkitSpeechRecognition = jest.fn(() => mockRecognition);
  });

  it('should not start recording when already recording', () => {
    const { result } = renderHook(() => useVoiceInput());

    act(() => {
      result.current.startRecording();
    });

    mockRecognition.start.mockClear();

    act(() => {
      result.current.startRecording();
    });

    expect(mockRecognition.start).not.toHaveBeenCalled();
  });

  it('should handle start recording error', () => {
    const onError = jest.fn();
    const { result } = renderHook(() => useVoiceInput({ onError }));

    mockRecognition.start.mockImplementation(() => {
      throw new Error('Start failed');
    });

    act(() => {
      result.current.startRecording();
    });

    expect(result.current.error).toBe('Start failed');
    expect(result.current.isRecording).toBe(false);
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
  });

  it('should configure recognition with custom options', () => {
    renderHook(() => useVoiceInput({
      language: 'es-ES',
      continuous: true,
      interimResults: false
    }));

    expect(mockRecognition.lang).toBe('es-ES');
    expect(mockRecognition.continuous).toBe(true);
    expect(mockRecognition.interimResults).toBe(false);
  });

  it('should cleanup on unmount', () => {
    const { result, unmount } = renderHook(() => useVoiceInput());

    act(() => {
      result.current.startRecording();
    });

    unmount();

    expect(mockRecognition.abort).toHaveBeenCalled();
  });

  it('should track voice input end with transcript length', () => {
    const { result } = renderHook(() => useVoiceInput());

    act(() => {
      result.current.startRecording();
    });

    act(() => {
      mockRecognition.simulateResult('Hello world', true);
    });

    act(() => {
      result.current.stopRecording();
    });

    expect(mockTrack).toHaveBeenCalledWith('voice_input_ended', {
      transcriptLength: 11,
      language: 'en-US'
    });
  });
});