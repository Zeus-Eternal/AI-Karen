import React, { useState, useRef, useEffect } from 'react';
import { useVoice } from '../../services/VoiceService';

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
  className?: string;
  onRecordingComplete?: (audioBlob: Blob, transcript: string) => void;
  onRecordingStart?: () => void;
  onRecordingCancel?: () => void;
  onError?: (error: string) => void;
  maxRecordingTime?: number; // in seconds
  showTranscript?: boolean;
  showVisualization?: boolean;
  autoTranscribe?: boolean;
  language?: string;
  disabled?: boolean;
}

// Audio visualization component
const AudioVisualization: React.FC<{
  audioStream: MediaStream | null;
  isRecording: boolean;
  theme: Theme;
}> = ({ audioStream, isRecording, theme }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number>(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  
  useEffect(() => {
    if (!audioStream || !canvasRef.current || !isRecording) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = 0;
      }
      return;
    }
    
    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext('2d');
    if (!canvasCtx) return;
    
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    
    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);
    
    analyserRef.current = analyser;
    
    const bufferLength = analyser.frequencyBinCount;
    dataArrayRef.current = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!isRecording) return;
      
      animationFrameRef.current = requestAnimationFrame(draw);
      
      const dataArray = dataArrayRef.current;
      if (dataArray) {
        analyser.getByteFrequencyData(dataArray as Uint8Array<ArrayBuffer>);
      }
      
      canvasCtx.fillStyle = theme.colors.background;
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
      
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;
      
      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray ? (dataArray[i] ?? 0) / 2 : 0;
        
        const gradient = canvasCtx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, theme.colors.primary);
        gradient.addColorStop(1, theme.colors.secondary);
        
        canvasCtx.fillStyle = gradient;
        canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        
        x += barWidth + 1;
      }
    };
    
    draw();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      source.disconnect();
      analyser.disconnect();
      if (audioContext.state !== 'closed') {
        audioContext.close();
      }
    };
  }, [audioStream, isRecording, theme]);
  
  return (
    <canvas
      ref={canvasRef}
      className="copilot-audio-visualization"
      style={{
        width: '100%',
        height: '60px',
        borderRadius: theme.borderRadius,
        backgroundColor: theme.colors.background,
        border: `1px solid ${theme.colors.border}`
      }}
    />
  );
};

// Format time for display
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};


export const VoiceRecorderComponent: React.FC<VoiceRecorderProps> = ({
  theme,
  className = '',
  onRecordingComplete,
  onRecordingStart,
  onRecordingCancel,
  onError,
  maxRecordingTime = 300, // 5 minutes default
  showTranscript = true,
  showVisualization = true,
  autoTranscribe = true,
  language = 'en-US',
  disabled = false
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const {
    isRecording,
    isSupported,
    transcript,
    isProcessing,
    error,
    audioUrl,
    audioBlob,
    audioStream,
    recordingTime,
    startRecording,
    stopRecording,
    cancelRecording,
    resetRecording
  } = useVoice({
    language,
    autoTranscribe,
    maxRecordingTime,
    onRecordingComplete,
    onRecordingStart,
    onRecordingCancel,
    onError
  });
  
  // Play recorded audio
  const playAudio = () => {
    if (audioRef.current && audioUrl) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };
  
  // Pause audio
  const pauseAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };
  
  // Submit recording
  const submitRecording = () => {
    if (audioBlob && onRecordingComplete) {
      onRecordingComplete(audioBlob, transcript);
      resetRecording();
    }
  };
  
  // Format recording time
  const formattedTime = formatTime(recordingTime);
  const timeRemaining = maxRecordingTime - recordingTime;
  const formattedTimeRemaining = formatTime(timeRemaining);
  
  const containerStyle: React.CSSProperties = {
    width: '100%',
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    padding: theme.spacing.md,
    boxShadow: theme.shadows.sm,
    ...(disabled ? {
      opacity: 0.7,
      cursor: 'not-allowed'
    } : {})
  };
  
  const buttonStyle: React.CSSProperties = {
    backgroundColor: 'transparent',
    color: theme.colors.textSecondary,
    border: 'none',
    borderRadius: '50%',
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    fontSize: '1.2rem',
    transition: 'all 0.2s ease',
    ...(disabled ? {
      cursor: 'not-allowed',
      opacity: 0.5
    } : {})
  };
  
  const recordButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: isRecording ? theme.colors.error : theme.colors.primary,
    color: '#fff',
    width: '64px',
    height: '64px',
    boxShadow: theme.shadows.md
  };
  
  return (
    <div
      className={`copilot-voice-recorder ${className}`}
      style={containerStyle}
      role="region"
      aria-label="Voice recorder"
      aria-busy={isRecording || isProcessing}
    >
      {/* Hidden audio element for playback */}
      <audio
        ref={audioRef}
        src={audioUrl || undefined}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
      
      {/* Recording status and time */}
      <div
        className="copilot-recording-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: theme.spacing.md
        }}
        role="status"
        aria-live="polite"
      >
        <div
          className="copilot-recording-status"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.sm
          }}
        >
          <div
            className="copilot-status-indicator"
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: isRecording 
                ? theme.colors.error 
                : isProcessing 
                  ? theme.colors.warning 
                  : theme.colors.success,
              animation: isRecording ? 'pulse 1.5s infinite' : 'none'
            }}
          />
          <span
            className="copilot-status-text"
            style={{
              fontSize: theme.typography.fontSize.sm,
              fontWeight: theme.typography.fontWeight.medium,
              color: theme.colors.text
            }}
          >
            {isRecording 
              ? 'Recording...' 
              : isProcessing 
                ? 'Processing...' 
                : audioBlob 
                  ? 'Recording Complete' 
                  : 'Ready to Record'}
          </span>
        </div>
        
        {isRecording && (
          <div
            className="copilot-recording-time"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.sm
            }}
          >
            <span
              className="copilot-time-elapsed"
              style={{
                fontSize: theme.typography.fontSize.sm,
                fontWeight: theme.typography.fontWeight.medium,
                color: theme.colors.text
              }}
            >
              {formattedTime}
            </span>
            <span
              className="copilot-time-separator"
              style={{
                fontSize: theme.typography.fontSize.sm,
                color: theme.colors.textSecondary
              }}
            >
              /
            </span>
            <span
              className="copilot-time-remaining"
              style={{
                fontSize: theme.typography.fontSize.sm,
                color: timeRemaining < 30 
                  ? theme.colors.error 
                  : theme.colors.textSecondary
              }}
            >
              {formattedTimeRemaining}
            </span>
          </div>
        )}
      </div>
      
      {/* Audio visualization */}
      {showVisualization && (
        <div
          className="copilot-visualization-container"
          style={{
            marginBottom: theme.spacing.md
          }}
          role="region"
          aria-label="Audio visualization"
          aria-hidden={!isRecording}
        >
          <AudioVisualization
            audioStream={audioStream}
            isRecording={isRecording}
            theme={theme}
          />
        </div>
      )}
      
      {/* Transcript */}
      {showTranscript && transcript && (
        <div
          className="copilot-transcript-container"
          style={{
            marginBottom: theme.spacing.md,
            padding: theme.spacing.sm,
            backgroundColor: theme.colors.background,
            borderRadius: theme.borderRadius,
            border: `1px solid ${theme.colors.border}`
          }}
          role="region"
          aria-label="Transcript"
        >
          <div
            className="copilot-transcript-label"
            style={{
              fontSize: theme.typography.fontSize.sm,
              fontWeight: theme.typography.fontWeight.medium,
              color: theme.colors.textSecondary,
              marginBottom: theme.spacing.xs
            }}
          >
            Transcript:
          </div>
          <div
            className="copilot-transcript-text"
            style={{
              fontSize: theme.typography.fontSize.base,
              color: theme.colors.text,
              whiteSpace: 'pre-wrap',
              minHeight: '40px'
            }}
          >
            {transcript || (isRecording ? 'Listening...' : '')}
          </div>
        </div>
      )}
      
      {/* Audio playback controls */}
      {audioUrl && !isRecording && (
        <div
          className="copilot-audio-playback"
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: theme.spacing.md,
            padding: theme.spacing.sm,
            backgroundColor: theme.colors.background,
            borderRadius: theme.borderRadius,
            border: `1px solid ${theme.colors.border}`
          }}
          role="region"
          aria-label="Audio playback controls"
        >
          <button
            onClick={isPlaying ? pauseAudio : playAudio}
            className="copilot-play-pause-button"
            aria-label={isPlaying ? 'Pause audio' : 'Play audio'}
            disabled={disabled}
            style={buttonStyle}
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>
          
          <div
            className="copilot-audio-info"
            style={{
              marginLeft: theme.spacing.sm,
              flex: 1
            }}
          >
            <div
              className="copilot-audio-label"
              style={{
                fontSize: theme.typography.fontSize.sm,
                fontWeight: theme.typography.fontWeight.medium,
                color: theme.colors.text
              }}
            >
              Recorded Audio
            </div>
            <div
              className="copilot-audio-duration"
              style={{
                fontSize: theme.typography.fontSize.xs,
                color: theme.colors.textSecondary
              }}
            >
              Duration: {formattedTime}
            </div>
          </div>
        </div>
      )}
      
      {/* Action buttons */}
      <div
        className="copilot-recording-actions"
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: theme.spacing.md
        }}
        role="group"
        aria-label="Recording actions"
      >
        {!isRecording && !audioBlob && (
          <button
            onClick={startRecording}
            className="copilot-record-button"
            aria-label="Start recording"
            disabled={disabled}
            style={recordButtonStyle}
            onMouseEnter={(e) => {
              if (!disabled) {
                e.currentTarget.style.transform = 'scale(1.05)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
            }}
            tabIndex={0}
          >
            🎤
          </button>
        )}
        
        {isRecording && (
          <button
            onClick={stopRecording}
            className="copilot-stop-button"
            aria-label="Stop recording"
            disabled={disabled}
            style={recordButtonStyle}
            tabIndex={0}
          >
            ⏹️
          </button>
        )}
        
        {isRecording && (
          <button
            onClick={cancelRecording}
            className="copilot-cancel-button"
            aria-label="Cancel recording"
            disabled={disabled}
            style={buttonStyle}
            onMouseEnter={(e) => {
              if (!disabled) {
                e.currentTarget.style.backgroundColor = theme.colors.error + '20';
                e.currentTarget.style.color = theme.colors.error;
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = theme.colors.textSecondary;
            }}
            tabIndex={0}
          >
            ✕
          </button>
        )}
        
        {audioBlob && !isRecording && (
          <>
            <button
              onClick={submitRecording}
              className="copilot-submit-button"
              aria-label="Submit recording"
              disabled={disabled || isProcessing}
              style={{
                ...buttonStyle,
                backgroundColor: theme.colors.success,
                color: '#fff'
              }}
              onMouseEnter={(e) => {
                if (!disabled && !isProcessing) {
                  e.currentTarget.style.transform = 'scale(1.05)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
              }}
              tabIndex={0}
            >
              ✓
            </button>
            
            <button
              onClick={resetRecording}
              className="copilot-reset-button"
              aria-label="Reset recording"
              disabled={disabled}
              style={buttonStyle}
              onMouseEnter={(e) => {
                if (!disabled) {
                  e.currentTarget.style.backgroundColor = theme.colors.warning + '20';
                  e.currentTarget.style.color = theme.colors.warning;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.color = theme.colors.textSecondary;
              }}
              tabIndex={0}
            >
              🔄
            </button>
          </>
        )}
      </div>
      
      {/* Error message */}
      {!isSupported && autoTranscribe && (
        <div
          className="copilot-speech-warning"
          style={{
            marginTop: theme.spacing.sm,
            padding: theme.spacing.sm,
            backgroundColor: theme.colors.warning + '20',
            borderRadius: theme.borderRadius,
            fontSize: theme.typography.fontSize.sm,
            color: theme.colors.warning,
            textAlign: 'center'
          }}
          role="alert"
          aria-live="polite"
        >
          Speech recognition is not supported in your browser. You can still record audio but won't get automatic transcription.
        </div>
      )}
      
      {/* Error display */}
      {error && (
        <div
          className="copilot-recording-error"
          style={{
            marginTop: theme.spacing.sm,
            padding: theme.spacing.sm,
            backgroundColor: theme.colors.error + '20',
            borderRadius: theme.borderRadius,
            fontSize: theme.typography.fontSize.sm,
            color: theme.colors.error,
            textAlign: 'center'
          }}
          role="alert"
          aria-live="assertive"
        >
          {error}
        </div>
      )}
      
      <style jsx>{`
        @keyframes pulse {
          0% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.7;
            transform: scale(1.1);
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

export default VoiceRecorderComponent;