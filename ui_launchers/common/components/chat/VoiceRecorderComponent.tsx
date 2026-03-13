import React, { useState, useEffect, useRef } from 'react';

// Type definitions
interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

interface VoiceRecorderProps {
  theme: Theme;
  isRecording?: boolean;
  onRecordingStart?: () => void;
  onRecordingStop?: (transcript: string) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

interface VoiceRecorderState {
  isRecording: boolean;
  isSupported: boolean;
  hasPermission: boolean | null;
  transcript: string;
  interimTranscript: string;
  confidence: number;
  duration: number;
  error: string | null;
  audioLevel: number;
}

// Default theme
const defaultTheme: Theme = {
  colors: {
    primary: '#3b82f6',
    secondary: '#64748b',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
    textSecondary: '#64748b',
    border: '#e2e8f0',
    error: '#ef4444',
    warning: '#f59e0b',
    success: '#10b981',
    info: '#3b82f6'
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    xxl: '3rem'
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      xxl: '1.5rem'
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700
    }
  },
  borderRadius: '0.5rem',
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
  }
};

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  theme = defaultTheme,
  isRecording: controlledIsRecording = false,
  onRecordingStart,
  onRecordingStop,
  onError,
  disabled = false,
  className = ''
}) => {
  const [state, setState] = useState<VoiceRecorderState>({
    isRecording: controlledIsRecording,
    isSupported: false,
    hasPermission: null,
    transcript: '',
    interimTranscript: '',
    confidence: 0,
    duration: 0,
    error: null,
    audioLevel: 0
  });

  const recognitionRef = useRef<any>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const durationTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check if speech recognition is supported
  useEffect(() => {
    const isSupported = typeof window !== 'undefined' && 
      (window.SpeechRecognition || (window as any).webkitSpeechRecognition);
    
    setState(prev => ({ ...prev, isSupported }));
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (!state.isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setState(prev => ({
        ...prev,
        isRecording: true,
        error: null,
        transcript: '',
        interimTranscript: '',
        duration: 0
      }));

      // Start duration timer
      durationTimerRef.current = setInterval(() => {
        setState(prev => ({ ...prev, duration: prev.duration + 1 }));
      }, 1000);

      if (onRecordingStart) {
        onRecordingStart();
      }
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        const confidence = event.results[i][0].confidence;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
          setState(prev => ({ 
            ...prev, 
            transcript: finalTranscript,
            confidence: confidence || 0
          }));
        } else {
          interimTranscript += transcript;
          setState(prev => ({ ...prev, interimTranscript }));
        }
      }
    };

    recognition.onerror = (event: any) => {
      const errorMessage = getErrorMessage(event.error);
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isRecording: false
      }));

      cleanup();

      if (onError) {
        onError(errorMessage);
      }
    };

    recognition.onend = () => {
      setState(prev => ({ ...prev, isRecording: false }));
      cleanup();
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      cleanup();
    };
  }, [state.isSupported, onRecordingStart, onError]);

  // Handle controlled isRecording prop
  useEffect(() => {
    if (controlledIsRecording !== state.isRecording) {
      if (controlledIsRecording) {
        startRecording();
      } else {
        stopRecording();
      }
    }
  }, [controlledIsRecording]);

  // Cleanup function
  const cleanup = () => {
    if (durationTimerRef.current) {
      clearInterval(durationTimerRef.current);
      durationTimerRef.current = null;
    }

    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
  };

  // Start recording
  const startRecording = async () => {
    if (!state.isSupported || disabled) {
      const error = 'Speech recognition is not supported in this browser';
      setState(prev => ({ ...prev, error }));
      if (onError) {
        onError(error);
      }
      return;
    }

    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      
      setState(prev => ({ ...prev, hasPermission: true }));

      // Initialize audio context for visualization
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      
      analyser.fftSize = 256;
      const microphone = audioContext.createMediaStreamSource(stream);
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      // Start visualization
      visualizeAudio();

      // Start recognition
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        hasPermission: false
      }));
      
      if (onError) {
        onError(errorMessage);
      }
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (recognitionRef.current && state.isRecording) {
      recognitionRef.current.stop();
    }

    setState(prev => ({ ...prev, isRecording: false }));

    if (onRecordingStop && state.transcript) {
      onRecordingStop(state.transcript);
    }

    cleanup();
  };

  // Toggle recording
  const toggleRecording = () => {
    if (state.isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Visualize audio
  const visualizeAudio = () => {
    if (!analyserRef.current) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const update = () => {
      animationRef.current = requestAnimationFrame(update);
      
      analyser.getByteFrequencyData(dataArray);
      
      // Calculate average audio level
      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i];
      }
      const average = sum / bufferLength;
      const normalizedLevel = average / 255;
      
      setState(prev => ({ ...prev, audioLevel: normalizedLevel }));
    };

    update();
  };

  // Get error message from error code
  const getErrorMessage = (errorCode: string): string => {
    const errorMessages: Record<string, string> = {
      'no-speech': 'No speech was detected. Please try again.',
      'audio-capture': 'Audio capture failed. Please check your microphone.',
      'not-allowed': 'Microphone access was denied. Please enable microphone permissions.',
      'network': 'Network error occurred during speech recognition.',
      'service-not-allowed': 'Speech recognition service is not allowed.',
      'bad-grammar': 'Speech recognition grammar error.',
      'language-not-supported': 'The specified language is not supported.'
    };

    return errorMessages[errorCode] || `Speech recognition error: ${errorCode}`;
  };

  // Format duration
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      className={`karen-voice-recorder ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: theme.spacing.md,
        backgroundColor: theme.colors.surface,
        borderRadius: theme.borderRadius,
        border: `1px solid ${theme.colors.border}`,
        boxShadow: theme.shadows.sm
      }}
    >
      <button
        onClick={toggleRecording}
        disabled={disabled || !state.isSupported}
        className="karen-voice-button"
        aria-label={state.isRecording ? 'Stop recording' : 'Start voice input'}
        style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: state.isRecording 
            ? theme.colors.error 
            : theme.colors.primary,
          color: 'white',
          border: 'none',
          cursor: (disabled || !state.isSupported) ? 'not-allowed' : 'pointer',
          opacity: (disabled || !state.isSupported) ? 0.5 : 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '24px',
          marginBottom: theme.spacing.md,
          transition: 'all 0.2s ease',
          transform: state.isRecording ? 'scale(1.1)' : 'scale(1)',
          boxShadow: state.isRecording ? `0 0 0 4px ${theme.colors.error}40` : 'none'
        }}
      >
        {state.isRecording ? '●' : '🎤'}
      </button>

      {state.isRecording && (
        <div 
          className="karen-recording-status"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%'
          }}
        >
          <div 
            className="karen-recording-indicator"
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: theme.spacing.sm
            }}
          >
            <div 
              className="karen-recording-dot"
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: theme.colors.error,
                marginRight: theme.spacing.xs,
                animation: 'pulse 1.5s infinite'
              }}
            />
            <span style={{ fontSize: theme.typography.fontSize.sm, color: theme.colors.textSecondary }}>
              Recording... {formatDuration(state.duration)}
            </span>
          </div>

          {/* Audio level visualization */}
          <div 
            className="karen-audio-visualizer"
            style={{
              width: '100%',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: theme.spacing.sm
            }}
          >
            <div 
              className="karen-audio-bar"
              style={{
                width: '100%',
                height: '4px',
                backgroundColor: theme.colors.border,
                borderRadius: '2px',
                overflow: 'hidden',
                position: 'relative'
              }}
            >
              <div 
                className="karen-audio-level"
                style={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  height: '100%',
                  width: `${state.audioLevel * 100}%`,
                  backgroundColor: theme.colors.primary,
                  transition: 'width 0.1s ease'
                }}
              />
            </div>
          </div>

          {/* Interim transcript */}
          {state.interimTranscript && (
            <div 
              className="karen-interim-transcript"
              style={{
                padding: theme.spacing.sm,
                backgroundColor: theme.colors.background,
                borderRadius: theme.borderRadius,
                border: `1px solid ${theme.colors.border}`,
                width: '100%',
                minHeight: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <span style={{ 
                fontSize: theme.typography.fontSize.sm, 
                color: theme.colors.textSecondary,
                fontStyle: 'italic'
              }}>
                {state.interimTranscript}
              </span>
            </div>
          )}
        </div>
      )}

      {state.error && (
        <div 
          className="karen-recording-error"
          style={{
            marginTop: theme.spacing.sm,
            padding: theme.spacing.sm,
            backgroundColor: `${theme.colors.error}10`,
            color: theme.colors.error,
            borderRadius: theme.borderRadius,
            border: `1px solid ${theme.colors.error}20`,
            fontSize: theme.typography.fontSize.sm,
            width: '100%',
            textAlign: 'center'
          }}
        >
          {state.error}
        </div>
      )}

      {!state.isSupported && (
        <div 
          className="karen-voice-unsupported"
          style={{
            marginTop: theme.spacing.sm,
            padding: theme.spacing.sm,
            backgroundColor: `${theme.colors.warning}10`,
            color: theme.colors.warning,
            borderRadius: theme.borderRadius,
            border: `1px solid ${theme.colors.warning}20`,
            fontSize: theme.typography.fontSize.sm,
            width: '100%',
            textAlign: 'center'
          }}
        >
          Voice input is not supported in your browser.
        </div>
      )}

      <style jsx>{`
        @keyframes pulse {
          0% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.2);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
};

export default VoiceRecorder;