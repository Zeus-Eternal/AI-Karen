/**
 * Voice Recognition Hook
 * Handles speech-to-text conversion with multiple provider support
 */

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { auditLogger } from '@/lib/audit-logger';

// Type declarations for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: SpeechRecognition | undefined;
    webkitSpeechRecognition: SpeechRecognition | undefined;
  }
}

interface SpeechRecognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onstart: () => void;
  onend: () => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onresult: (event: SpeechRecognitionEvent) => void;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent {
  error: {
    message: string;
    name: string;
    errorCode: number;
  };
}

// Voice recognition state
export interface VoiceRecognitionState {
  isSupported: boolean;
  isListening: boolean;
  isRecording: boolean;
  transcript: string;
  confidence: number;
  error?: string;
  provider: string;
}

// Voice recognition options
export interface VoiceRecognitionOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  provider?: 'web-speech-api' | 'whisper-local' | 'whisper-cloud';
}

// Hook return type
export interface UseVoiceRecognitionReturn {
  state: VoiceRecognitionState;
  startListening: () => Promise<void>;
  stopListening: () => void;
  toggleListening: () => void;
  clearTranscript: () => void;
  processWithWhisper: (audioBlob: Blob) => Promise<string>;
}

export function useVoiceRecognition(options: VoiceRecognitionOptions = {}): UseVoiceRecognitionReturn {
  const [state, setState] = useState<VoiceRecognitionState>({
    isSupported: false,
    isListening: false,
    isRecording: false,
    transcript: '',
    confidence: 0,
    error: undefined,
    provider: options.provider || 'web-speech-api',
  });
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  
  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setState(prev => ({ ...prev, isSupported: false, error: 'Speech recognition not supported in this browser' }));
      return;
    }
    
    setState(prev => ({ ...prev, isSupported: true }));
    recognitionRef.current = SpeechRecognition;
    
    // Configure recognition
    if (recognitionRef.current) {
      const recognition = recognitionRef.current;
      
      recognition.continuous = options.continuous ?? false;
      recognition.interimResults = options.interimResults ?? true;
      recognition.lang = options.language || 'en-US';
      recognition.maxAlternatives = options.maxAlternatives ?? 1;
      
      // Event handlers
      recognition.onstart = () => {
        setState(prev => ({ ...prev, isRecording: true, error: undefined }));
        auditLogger.log('INFO', 'VOICE_RECORDING_STARTED', {
          provider: options.provider || 'web-speech-api',
          details: { language: recognition.lang, continuous: recognition.continuous },
        });
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const result = event.results[0];
        if (result && result[0]) {
          const transcript = result[0].transcript;
          const confidence = result[0].confidence;
          
          setState(prev => ({
            ...prev,
            transcript: options.interimResults ? transcript : prev.transcript + transcript,
            confidence: Math.max(prev.confidence, confidence),
            isRecording: false,
          }));
          
          auditLogger.log('INFO', 'VOICE_TRANSCRIPT', {
            provider: options.provider || 'web-speech-api',
            details: { transcript, confidence, isFinal: !result.isFinal },
          });
        }
      };
      
      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        const error = event.error;
        setState(prev => ({ ...prev, isRecording: false, error: error.message }));
        
        auditLogger.log('ERROR', 'VOICE_ERROR', {
          provider: options.provider || 'web-speech-api',
          error: error.message,
          details: { error: error.name, code: error.errorCode },
        });
      };
      
      recognition.onend = () => {
        setState(prev => ({ ...prev, isRecording: false, isListening: false }));
        auditLogger.log('INFO', 'VOICE_RECORDING_ENDED', {
          provider: options.provider || 'web-speech-api',
        });
      };
    }
  }, [options.continuous, options.interimResults, options.language, options.maxAlternatives, options.provider]);
  
  // Start listening
  const startListening = useCallback(async () => {
    if (!state.isSupported || !recognitionRef.current) {
      setState(prev => ({ ...prev, error: 'Voice recognition not available' }));
      return;
    }
    
    try {
      if (recognitionRef.current) {
        recognitionRef.current.start();
        setState(prev => ({ ...prev, isListening: true, error: undefined }));
      }
    } catch (error) {
      setState(prev => ({ ...prev, isListening: false, error: error instanceof Error ? error.message : 'Failed to start listening' }));
      auditLogger.log('ERROR', 'VOICE_START_ERROR', {
        provider: options.provider || 'web-speech-api',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }, [state.isSupported, options.provider]);
  
  // Stop listening
  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    
    try {
      recognitionRef.current.stop();
      setState(prev => ({ ...prev, isListening: false, isRecording: false }));
    } catch (error) {
      setState(prev => ({ ...prev, error: error instanceof Error ? error.message : 'Failed to stop listening' }));
      auditLogger.log('ERROR', 'VOICE_STOP_ERROR', {
        provider: options.provider || 'web-speech-api',
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }, [options.provider]);
  
  // Toggle listening
  const toggleListening = useCallback(() => {
    if (state.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [state.isListening, startListening, stopListening]);
  
  // Clear transcript
  const clearTranscript = useCallback(() => {
    setState(prev => ({ ...prev, transcript: '', confidence: 0 }));
  }, []);
  
  // Whisper cloud processing (alternative to browser API)
  const processWithWhisper = useCallback(async (audioBlob: Blob): Promise<string> => {
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('language', options.language || 'en');
      formData.append('model', 'whisper-1');
      
      // Send to Whisper API (would be configured endpoint)
      const response = await fetch('/api/ai/transcribe', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Whisper API error: ${response.statusText}`);
      }
      
      const result = await response.json();
      return result.transcript || '';
    } catch (error) {
      console.error('Whisper processing error:', error);
      throw error instanceof Error ? error : new Error('Unknown error occurred');
    }
  }, [options.language]);
  
  return {
    state,
    startListening,
    stopListening,
    toggleListening,
    clearTranscript,
    processWithWhisper,
  };
}
