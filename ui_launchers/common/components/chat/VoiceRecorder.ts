// Shared Voice Recorder Component
// Framework-agnostic voice recording functionality

import { Theme } from '../../abstractions/types';
import { errorHandler, debounce } from '../../abstractions/utils';

export interface VoiceRecorderOptions {
  autoStart?: boolean;
  maxDuration?: number; // in seconds
  enableVisualizer?: boolean;
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
}

export interface VoiceRecorderState {
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

export interface VoiceRecorderCallbacks {
  onStart?: () => void;
  onStop?: () => void;
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
  onPermissionChange?: (hasPermission: boolean) => void;
}

export class SharedVoiceRecorder {
  private state: VoiceRecorderState;
  private options: VoiceRecorderOptions;
  private callbacks: VoiceRecorderCallbacks;
  private theme: Theme;
  
  private recognition: any = null;
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private microphone: MediaStreamAudioSourceNode | null = null;
  private dataArray: Uint8Array | null = null;
  
  private durationTimer: NodeJS.Timeout | null = null;
  private visualizerTimer: NodeJS.Timeout | null = null;
  private debouncedResult: (transcript: string, isFinal: boolean) => void;

  constructor(
    theme: Theme,
    options: VoiceRecorderOptions = {},
    callbacks: VoiceRecorderCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      autoStart: false,
      maxDuration: 60,
      enableVisualizer: true,
      language: 'en-US',
      continuous: false,
      interimResults: true,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      isRecording: false,
      isSupported: this.checkSupport(),
      hasPermission: null,
      transcript: '',
      interimTranscript: '',
      confidence: 0,
      duration: 0,
      error: null,
      audioLevel: 0
    };

    // Create debounced result handler
    this.debouncedResult = debounce((transcript: string, isFinal: boolean) => {
      if (this.callbacks.onResult) {
        this.callbacks.onResult(transcript, isFinal);
      }
    }, 100);

    this.initializeRecognition();
    
    if (this.options.autoStart) {
      this.start();
    }
  }

  // Get current state
  getState(): VoiceRecorderState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<VoiceRecorderState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Check if speech recognition is supported
  private checkSupport(): boolean {
    return !!(
      typeof window !== 'undefined' &&
      (window.SpeechRecognition || (window as any).webkitSpeechRecognition)
    );
  }

  // Initialize speech recognition
  private initializeRecognition(): void {
    if (!this.state.isSupported) return;

    const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();

    this.recognition.continuous = this.options.continuous;
    this.recognition.interimResults = this.options.interimResults;
    this.recognition.lang = this.options.language;

    this.recognition.onstart = () => {
      this.updateState({
        isRecording: true,
        error: null,
        transcript: '',
        interimTranscript: '',
        duration: 0
      });

      this.startDurationTimer();
      
      if (this.options.enableVisualizer) {
        this.startVisualizer();
      }

      if (this.callbacks.onStart) {
        this.callbacks.onStart();
      }
    };

    this.recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        const confidence = event.results[i][0].confidence;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
          this.updateState({ 
            transcript: finalTranscript,
            confidence: confidence || 0
          });
          this.debouncedResult(finalTranscript, true);
        } else {
          interimTranscript += transcript;
          this.updateState({ interimTranscript });
          this.debouncedResult(interimTranscript, false);
        }
      }
    };

    this.recognition.onerror = (event: any) => {
      const errorMessage = this.getErrorMessage(event.error);
      this.updateState({
        error: errorMessage,
        isRecording: false
      });

      this.cleanup();

      if (this.callbacks.onError) {
        this.callbacks.onError(errorMessage);
      }
    };

    this.recognition.onend = () => {
      this.updateState({ isRecording: false });
      this.cleanup();

      if (this.callbacks.onStop) {
        this.callbacks.onStop();
      }
    };
  }

  // Start recording
  async start(): Promise<void> {
    if (!this.state.isSupported) {
      const error = 'Speech recognition is not supported in this browser';
      this.updateState({ error });
      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
      return;
    }

    if (this.state.isRecording) {
      return;
    }

    try {
      // Request microphone permission
      await this.requestPermission();
      
      if (!this.state.hasPermission) {
        const error = 'Microphone permission denied';
        this.updateState({ error });
        if (this.callbacks.onError) {
          this.callbacks.onError(error);
        }
        return;
      }

      // Start recognition
      this.recognition.start();

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
      this.updateState({ error: errorMessage });
      if (this.callbacks.onError) {
        this.callbacks.onError(errorMessage);
      }
    }
  }

  // Stop recording
  stop(): void {
    if (!this.state.isRecording) return;

    if (this.recognition) {
      this.recognition.stop();
    }

    this.cleanup();
  }

  // Toggle recording
  async toggle(): Promise<void> {
    if (this.state.isRecording) {
      this.stop();
    } else {
      await this.start();
    }
  }

  // Request microphone permission
  private async requestPermission(): Promise<void> {
    try {
      // Check if permission is already granted
      if (navigator.permissions) {
        const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
        
        if (permission.state === 'granted') {
          this.updateState({ hasPermission: true });
          return;
        }
        
        if (permission.state === 'denied') {
          this.updateState({ hasPermission: false });
          return;
        }
      }

      // Request permission by accessing microphone
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaStream = stream;
      this.updateState({ hasPermission: true });

      if (this.callbacks.onPermissionChange) {
        this.callbacks.onPermissionChange(true);
      }

    } catch (error) {
      this.updateState({ hasPermission: false });
      
      if (this.callbacks.onPermissionChange) {
        this.callbacks.onPermissionChange(false);
      }
      
      throw error;
    }
  }

  // Start duration timer
  private startDurationTimer(): void {
    this.durationTimer = setInterval(() => {
      const newDuration = this.state.duration + 1;
      this.updateState({ duration: newDuration });

      // Auto-stop if max duration reached
      if (this.options.maxDuration && newDuration >= this.options.maxDuration) {
        this.stop();
      }
    }, 1000);
  }

  // Start audio visualizer
  private async startVisualizer(): Promise<void> {
    if (!this.mediaStream || !this.options.enableVisualizer) return;

    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.microphone = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      this.analyser.fftSize = 256;
      const bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(bufferLength);
      
      this.microphone.connect(this.analyser);
      
      this.updateAudioLevel();
      
    } catch (error) {
      console.warn('Failed to initialize audio visualizer:', error);
    }
  }

  // Update audio level for visualizer
  private updateAudioLevel(): void {
    if (!this.analyser || !this.dataArray) return;

    this.visualizerTimer = setInterval(() => {
      if (!this.state.isRecording) return;

      this.analyser!.getByteFrequencyData(this.dataArray!);
      
      // Calculate average audio level
      let sum = 0;
      for (let i = 0; i < this.dataArray!.length; i++) {
        sum += this.dataArray![i];
      }
      const average = sum / this.dataArray!.length;
      const normalizedLevel = average / 255;
      
      this.updateState({ audioLevel: normalizedLevel });
    }, 100);
  }

  // Clean up resources
  private cleanup(): void {
    if (this.durationTimer) {
      clearInterval(this.durationTimer);
      this.durationTimer = null;
    }

    if (this.visualizerTimer) {
      clearInterval(this.visualizerTimer);
      this.visualizerTimer = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.analyser = null;
    this.microphone = null;
    this.dataArray = null;
  }

  // Get error message from error code
  private getErrorMessage(errorCode: string): string {
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
  }

  // Get formatted duration
  getFormattedDuration(): string {
    const minutes = Math.floor(this.state.duration / 60);
    const seconds = this.state.duration % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-voice-recorder'];
    
    if (this.state.isRecording) {
      classes.push('karen-voice-recorder-recording');
    }
    
    if (this.state.error) {
      classes.push('karen-voice-recorder-error');
    }
    
    if (!this.state.isSupported) {
      classes.push('karen-voice-recorder-unsupported');
    }
    
    return classes;
  }

  // Get inline styles
  getInlineStyles(): Record<string, string> {
    return {
      backgroundColor: this.state.isRecording 
        ? this.theme.colors.error 
        : this.theme.colors.primary,
      color: 'white',
      border: 'none',
      borderRadius: this.theme.borderRadius,
      padding: this.theme.spacing.sm,
      cursor: this.state.isSupported ? 'pointer' : 'not-allowed',
      opacity: this.state.isSupported ? '1' : '0.5',
      transition: 'all 0.2s ease'
    };
  }

  // Get render data
  getRenderData(): VoiceRecorderRenderData {
    return {
      state: this.getState(),
      options: this.options,
      formattedDuration: this.getFormattedDuration(),
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onStart: () => this.start(),
        onStop: () => this.stop(),
        onToggle: () => this.toggle()
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }

  // Destroy the recorder
  destroy(): void {
    this.stop();
    this.cleanup();
  }
}

// Supporting interfaces
export interface VoiceRecorderRenderData {
  state: VoiceRecorderState;
  options: VoiceRecorderOptions;
  formattedDuration: string;
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onStart: () => Promise<void>;
    onStop: () => void;
    onToggle: () => Promise<void>;
  };
}

// Utility functions
export function createVoiceRecorder(
  theme: Theme,
  options: VoiceRecorderOptions = {},
  callbacks: VoiceRecorderCallbacks = {}
): SharedVoiceRecorder {
  return new SharedVoiceRecorder(theme, options, callbacks);
}

export function isVoiceRecordingSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    (window.SpeechRecognition || (window as any).webkitSpeechRecognition) &&
    navigator.mediaDevices &&
    navigator.mediaDevices.getUserMedia
  );
}

export function getVoiceRecordingPermissionStatus(): Promise<PermissionState | null> {
  if (!navigator.permissions) {
    return Promise.resolve(null);
  }

  return navigator.permissions
    .query({ name: 'microphone' as PermissionName })
    .then(permission => permission.state)
    .catch(() => null);
}