# Path: ui_launchers/web_ui/src/hooks/use-voice-input.ts

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useTelemetry } from '@/hooks/use-telemetry';

interface VoiceInputOptions {
  onTranscript?: (transcript: string) => void;
  onError?: (error: Error) => void;
  onStart?: () => void;
  onEnd?: () => void;
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
}

interface VoiceInputState {
  isRecording: boolean;
  isSupported: boolean;
  transcript: string;
  interimTranscript: string;
  error: string | null;
}

interface VoiceInputActions {
  startRecording: () => void;
  stopRecording: () => void;
  clearTranscript: () => void;
}

export const useVoiceInput = (options: VoiceInputOptions = {}): VoiceInputState & VoiceInputActions => {
  const {
    onTranscript,
    onError,
    onStart,
    onEnd,
    language = 'en-US',
    continuous = false,
    interimResults = true
  } = options;

  const { track } = useTelemetry();
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const [state, setState] = useState<VoiceInputState>({
    isRecording: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
    error: null
  });

  // Check for browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const isSupported = !!SpeechRecognition;

    setState(prev => ({ ...prev, isSupported }));

    if (isSupported) {
      const recognition = new SpeechRecognition();
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;

      // Handle results
      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setState(prev => ({
          ...prev,
          transcript: prev.transcript + finalTranscript,
          interimTranscript
        }));

        if (finalTranscript) {
          onTranscript?.(finalTranscript);
          track('voice_input_transcript', {
            transcriptLength: finalTranscript.length,
            language
          });
        }
      };

      // Handle start
      recognition.onstart = () => {
        setState(prev => ({ ...prev, isRecording: true, error: null }));
        onStart?.();
        track('voice_input_started', { language });
      };

      // Handle end
      recognition.onend = () => {
        setState(prev => ({ ...prev, isRecording: false }));
        onEnd?.();
        track('voice_input_ended', {
          transcriptLength: state.transcript.length,
          language
        });
      };

      // Handle errors
      recognition.onerror = (event) => {
        const error = new Error(`Speech recognition error: ${event.error}`);
        setState(prev => ({ 
          ...prev, 
          isRecording: false, 
          error: error.message 
        }));
        onError?.(error);
        track('voice_input_error', {
          error: event.error,
          language
        });
      };

      // Handle no speech
      recognition.onnomatch = () => {
        const error = new Error('No speech was detected');
        setState(prev => ({ 
          ...prev, 
          error: error.message 
        }));
        onError?.(error);
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language, continuous, interimResults, onTranscript, onError, onStart, onEnd, track]);

  // Start recording
  const startRecording = useCallback(() => {
    if (!state.isSupported) {
      const error = new Error('Speech recognition is not supported in this browser');
      setState(prev => ({ ...prev, error: error.message }));
      onError?.(error);
      return;
    }

    if (!recognitionRef.current || state.isRecording) {
      return;
    }

    try {
      // Clear previous transcript
      setState(prev => ({ 
        ...prev, 
        transcript: '', 
        interimTranscript: '', 
        error: null 
      }));

      recognitionRef.current.start();
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to start recording');
      setState(prev => ({ 
        ...prev, 
        error: err.message,
        isRecording: false 
      }));
      onError?.(err);
    }
  }, [state.isSupported, state.isRecording, onError]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (recognitionRef.current && state.isRecording) {
      recognitionRef.current.stop();
    }
  }, [state.isRecording]);

  // Clear transcript
  const clearTranscript = useCallback(() => {
    setState(prev => ({ 
      ...prev, 
      transcript: '', 
      interimTranscript: '',
      error: null 
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current && state.isRecording) {
        recognitionRef.current.abort();
      }
    };
  }, [state.isRecording]);

  return {
    ...state,
    startRecording,
    stopRecording,
    clearTranscript
  };
};

export default useVoiceInput;