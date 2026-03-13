/**
 * Service for handling voice input with proper error handling
 */
import React from 'react';
import ErrorHandlingService from './ErrorHandlingService';
import ErrorLoggingService from './ErrorLoggingService';
import UserErrorMessageService from './UserErrorMessageService';
import ErrorNotificationService from './ErrorNotificationService';
import { ErrorCategory, ErrorSeverity } from './ErrorHandlingService';
import { LogLevel, LogCategory } from './ErrorLoggingService';

// Web Speech API types
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onstart: (() => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
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

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

export class VoiceService {
  private static instance: VoiceService;
  private recognition: SpeechRecognition | null = null;
  private isSupported: boolean = false;
  private isListening: boolean = false;
  private onResult?: (transcript: string, isFinal: boolean) => void;
  private onError?: (error: string) => void;
  private onStart?: () => void;
  private onEnd?: () => void;
  private errorHandlingService: ErrorHandlingService;
  private errorLoggingService: ErrorLoggingService;
  private userErrorMessageService: UserErrorMessageService;
  private errorNotificationService: ErrorNotificationService;

  /**
   * Get singleton instance of VoiceService
   */
  public static getInstance(): VoiceService {
    if (!VoiceService.instance) {
      VoiceService.instance = new VoiceService();
    }
    return VoiceService.instance;
  }

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor() {
    this.errorHandlingService = ErrorHandlingService.getInstance();
    this.errorLoggingService = ErrorLoggingService.getInstance();
    this.userErrorMessageService = UserErrorMessageService.getInstance();
    this.errorNotificationService = ErrorNotificationService.getInstance();
    this.initialize();
  }

  /**
   * Initialize speech recognition
   */
  private initialize(): void {
    if (typeof window === 'undefined') {
      this.errorLoggingService.log(LogLevel.WARN, 'VoiceService: Window object not available', LogCategory.APPLICATION, {
        component: 'VoiceService',
        function: 'initialize'
      });
      return;
    }

    // Check for browser support
    const speechRecognitionWindow = window as Window & {
      SpeechRecognition?: new () => SpeechRecognition;
      webkitSpeechRecognition?: new () => SpeechRecognition;
    };
    const SpeechRecognitionConstructor =
      speechRecognitionWindow.SpeechRecognition || speechRecognitionWindow.webkitSpeechRecognition;
    
    if (!SpeechRecognitionConstructor) {
      this.errorLoggingService.log(LogLevel.WARN, 'VoiceService: Speech recognition not supported in this browser', LogCategory.APPLICATION, {
        component: 'VoiceService',
        function: 'initialize'
      });
      this.isSupported = false;
      return;
    }

    try {
      this.recognition = new SpeechRecognitionConstructor();
      this.isSupported = true;
      
      // Configure recognition
      if (this.recognition) {
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        if (this.recognition) {
          this.recognition.lang = 'en-US';
        }
      }
      
      // Set up event handlers
      if (this.recognition) {
        this.recognition.onresult = this.handleResult.bind(this);
        this.recognition.onerror = this.handleError.bind(this);
        this.recognition.onstart = this.handleStart.bind(this);
        this.recognition.onend = this.handleEnd.bind(this);
      }
      
      this.errorLoggingService.log(LogLevel.INFO, 'VoiceService: Initialized successfully', LogCategory.APPLICATION, {
        component: 'VoiceService',
        function: 'initialize'
      });
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.HIGH,
        { component: 'VoiceService', function: 'initialize' },
        undefined,
        { showNotification: true, message: 'Failed to initialize speech recognition' }
      );
      this.isSupported = false;
    }
  }

  /**
   * Handle speech recognition result
   */
  private handleResult(event: SpeechRecognitionEvent): void {
    if (!this.onResult) return;

    let finalTranscript = '';
    let interimTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      if (result && result[0]) {
        const transcript = result[0].transcript;
        
        if (result.isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
    }

    // Call the result callback with both final and interim results
    this.onResult(finalTranscript || interimTranscript, !!finalTranscript);
  }

  /**
   * Handle speech recognition error
   */
  private handleError(event: SpeechRecognitionErrorEvent): void {
    this.errorLoggingService.log(LogLevel.WARN, `VoiceService: Speech recognition error: ${event.error}`, LogCategory.APPLICATION, {
      component: 'VoiceService',
      function: 'handleError',
      error: event.error
    });
    
    let errorMessage = 'An unknown error occurred';
    let errorCategory = ErrorCategory.UNKNOWN;
    let errorSeverity = ErrorSeverity.MEDIUM;
    
    switch (event.error) {
      case 'no-speech':
        errorMessage = 'No speech was detected';
        errorCategory = ErrorCategory.USER_INPUT;
        errorSeverity = ErrorSeverity.LOW;
        break;
      case 'audio-capture':
        errorMessage = 'Audio capture error - no microphone found';
        errorCategory = ErrorCategory.HARDWARE;
        errorSeverity = ErrorSeverity.HIGH;
        break;
      case 'not-allowed':
        errorMessage = 'Microphone permission denied';
        errorCategory = ErrorCategory.PERMISSION;
        errorSeverity = ErrorSeverity.HIGH;
        break;
      case 'network':
        errorMessage = 'Network error occurred';
        errorCategory = ErrorCategory.NETWORK;
        errorSeverity = ErrorSeverity.MEDIUM;
        break;
      case 'service-not-allowed':
        errorMessage = 'Speech recognition service not allowed';
        errorCategory = ErrorCategory.PERMISSION;
        errorSeverity = ErrorSeverity.MEDIUM;
        break;
      case 'bad-grammar':
        errorMessage = 'Grammar error in speech recognition';
        errorCategory = ErrorCategory.VALIDATION;
        errorSeverity = ErrorSeverity.LOW;
        break;
      case 'language-not-supported':
        errorMessage = 'Language not supported';
        errorCategory = ErrorCategory.VALIDATION;
        errorSeverity = ErrorSeverity.LOW;
        break;
      default:
        errorMessage = `Error: ${event.error}`;
        errorCategory = ErrorCategory.UNKNOWN;
        errorSeverity = ErrorSeverity.MEDIUM;
    }
    
    // Handle error with error handling service
    this.errorHandlingService.handleError(
      new Error(errorMessage),
      errorCategory,
      errorSeverity,
      { component: 'VoiceService', function: 'handleError', error: event.error },
      undefined,
      { showNotification: true, message: errorMessage }
    );
    
    // Get user-friendly error message
    const userErrorMessage = this.userErrorMessageService.getUserFriendlyError(
      `VOICE_${event.error.toUpperCase()}`.replace(/-/g, '_'),
      { component: 'VoiceService' }
    );
    
    if (this.onError) {
      this.onError(userErrorMessage.message);
    }
    
    // Show error notification
    this.errorNotificationService.showNotification(
      'Voice Recognition Error',
      userErrorMessage.message || 'Voice recognition error',
      errorSeverity
    );
    
    // Reset listening state
    this.isListening = false;
  }

  /**
   * Handle speech recognition start
   */
  private handleStart(): void {
    this.errorLoggingService.log(LogLevel.INFO, 'VoiceService: Speech recognition started', LogCategory.APPLICATION, {
      component: 'VoiceService',
      function: 'handleStart'
    });
    this.isListening = true;
    
    if (this.onStart) {
      this.onStart();
    }
  }

  /**
   * Handle speech recognition end
   */
  private handleEnd(): void {
    this.errorLoggingService.log(LogLevel.INFO, 'VoiceService: Speech recognition ended', LogCategory.APPLICATION, {
      component: 'VoiceService',
      function: 'handleEnd'
    });
    this.isListening = false;
    
    if (this.onEnd) {
      this.onEnd();
    }
  }

  /**
   * Check if speech recognition is supported
   */
  public isSpeechRecognitionSupported(): boolean {
    return this.isSupported;
  }

  /**
   * Check if currently listening
   */
  public isCurrentlyListening(): boolean {
    return this.isListening;
  }

  /**
   * Start listening
   */
  public startListening(
    onResult: (transcript: string, isFinal: boolean) => void,
    onError: (error: string) => void,
    onStart?: () => void,
    onEnd?: () => void,
    language?: string
  ): boolean {
    if (!this.isSupported || !this.recognition) {
      if (onError) {
        onError('Speech recognition is not supported in this browser');
      }
      return false;
    }

    if (this.isListening) {
      console.warn('VoiceService: Already listening');
      return false;
    }

    // Set language if provided
    if (language) {
      this.recognition.lang = language;
    }

    // Set callbacks
    this.onResult = onResult;
    this.onError = onError;
    this.onStart = onStart;
    this.onEnd = onEnd;

    try {
      this.recognition.start();
      return true;
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.MEDIUM,
        { component: 'VoiceService', function: 'startListening' },
        undefined,
        { showNotification: true, message: 'Failed to start speech recognition' }
      );
      
      if (onError) {
        const userErrorMessage = this.userErrorMessageService.getUserFriendlyError(
          'VOICE_START_FAILED',
          { component: 'VoiceService' }
        );
        onError(userErrorMessage.message);
      }
      return false;
    }
  }

  /**
   * Stop listening
   */
  public stopListening(): boolean {
    if (!this.isSupported || !this.recognition) {
      return false;
    }

    if (!this.isListening) {
      console.warn('VoiceService: Not currently listening');
      return false;
    }

    try {
      this.recognition.stop();
      return true;
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.LOW,
        { component: 'VoiceService', function: 'stopListening' }
      );
      return false;
    }
  }

  /**
   * Abort listening (immediately stops without processing)
   */
  public abortListening(): boolean {
    if (!this.isSupported || !this.recognition) {
      return false;
    }

    if (!this.isListening) {
      console.warn('VoiceService: Not currently listening');
      return false;
    }

    try {
      this.recognition.abort();
      return true;
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.UNKNOWN,
        ErrorSeverity.LOW,
        { component: 'VoiceService', function: 'abortListening' }
      );
      return false;
    }
  }

  /**
   * Set language for speech recognition
   */
  public setLanguage(language: string): boolean {
    if (!this.isSupported || !this.recognition) {
      return false;
    }

    this.recognition.lang = language;
    return true;
  }

  /**
   * Get available languages
   */
  public getAvailableLanguages(): string[] {
    if (!this.isSupported) {
      return [];
    }

    // Common languages that most speech recognition engines support
    return [
      'en-US', 'en-GB', 'en-AU', 'en-CA', 'en-IN',
      'es-ES', 'es-MX', 'es-AR',
      'fr-FR', 'fr-CA',
      'de-DE', 'de-AT',
      'it-IT',
      'ja-JP',
      'ko-KR',
      'zh-CN', 'zh-TW', 'zh-HK',
      'ru-RU',
      'pt-BR', 'pt-PT',
      'ar-SA',
      'hi-IN'
    ];
  }

  /**
   * Check if microphone permission is granted
   */
  public async checkMicrophonePermission(): Promise<'granted' | 'denied' | 'prompt'> {
    if (typeof navigator === 'undefined' || !navigator.permissions) {
      return 'prompt';
    }

    try {
      const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      return permission.state;
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.PERMISSION,
        ErrorSeverity.LOW,
        { component: 'VoiceService', function: 'checkMicrophonePermission' }
      );
      return 'prompt';
    }
  }

  /**
   * Request microphone permission
   */
  public async requestMicrophonePermission(): Promise<boolean> {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      console.error('VoiceService: Media devices not available');
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop the stream immediately after getting permission
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.PERMISSION,
        ErrorSeverity.HIGH,
        { component: 'VoiceService', function: 'requestMicrophonePermission' },
        undefined,
        { showNotification: true, message: 'Microphone permission denied' }
      );
      
      const userErrorMessage = this.userErrorMessageService.getUserFriendlyError(
        'MICROPHONE_PERMISSION_DENIED',
        { component: 'VoiceService' }
      );
      
      this.errorNotificationService.showNotification(
        'Microphone Permission Denied',
        userErrorMessage.message || 'Microphone permission denied',
        ErrorSeverity.HIGH
      );
      
      return false;
    }
  }

  /**
   * Get default language from browser
   */
  public getDefaultLanguage(): string {
    if (typeof navigator === 'undefined') {
      return 'en-US';
    }

    const browserLang = navigator.language;
    
    // Check if the browser language is in our supported list
    const supportedLanguages = this.getAvailableLanguages();
    if (supportedLanguages.includes(browserLang)) {
      return browserLang;
    }
    
    // Try to match just the language part (e.g., 'en' from 'en-US')
    const langPart = browserLang.split('-')[0];
    const supportedLang = supportedLanguages.find(lang => lang.startsWith(langPart || ''));
    
    return supportedLang || 'en-US';
  }

  /**
   * Test audio input devices
   */
  public async getAudioInputDevices(): Promise<MediaDeviceInfo[]> {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      return [];
    }

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter(device => device.kind === 'audioinput');
    } catch (error) {
      this.errorHandlingService.handleError(
        error,
        ErrorCategory.HARDWARE,
        ErrorSeverity.MEDIUM,
        { component: 'VoiceService', function: 'getAudioInputDevices' }
      );
      return [];
    }
  }
}

/**
 * Hook for using voice service in React components
 */
export const useVoice = (options: {
  language?: string;
  autoTranscribe?: boolean;
  maxRecordingTime?: number;
  onRecordingComplete?: (audioBlob: Blob, transcript: string) => void;
  onRecordingStart?: () => void;
  onRecordingCancel?: () => void;
  onError?: (error: string) => void;
} = {}) => {
  const voiceService = VoiceService.getInstance();
  
  // State for recording
  const [isRecording, setIsRecording] = React.useState(false);
  const [recordingTime, setRecordingTime] = React.useState(0);
  const [audioStream, setAudioStream] = React.useState<MediaStream | null>(null);
  const [audioBlob, setAudioBlob] = React.useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = React.useState<string | null>(null);
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [transcript, setTranscript] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  
  const mediaRecorderRef = React.useRef<MediaRecorder | null>(null);
  const audioChunksRef = React.useRef<Blob[]>([]);
  const timerRef = React.useRef<NodeJS.Timeout | null>(null);
  
  const {
    language = 'en-US',
    autoTranscribe = true,
    maxRecordingTime = 300,
    onRecordingComplete,
    onRecordingStart,
    onRecordingCancel,
    onError
  } = options;

  void onRecordingComplete;
  
  // Clean up on unmount
  React.useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [audioUrl, audioStream]);

  // Stop recording
  const stopRecording = React.useCallback(() => {
    if (!isRecording || !mediaRecorderRef.current) return;

    setIsProcessing(true);
    mediaRecorderRef.current.stop();

    // Stop speech recognition if it's active
    if (autoTranscribe && voiceService.isCurrentlyListening()) {
      voiceService.stopListening();
    }

    // Stop all tracks in the stream
    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop());
      setAudioStream(null);
    }

    setIsRecording(false);
  }, [isRecording, audioStream, autoTranscribe, voiceService]);
  
  // Handle recording timer
  React.useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= maxRecordingTime) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, maxRecordingTime, stopRecording]);
  
  // Start recording
  const startRecording = React.useCallback(async () => {
    if (isRecording) return;
    
    try {
      // Reset state
      setRecordingTime(0);
      audioChunksRef.current = [];
      setAudioBlob(null);
      setAudioUrl(null);
      setTranscript('');
      setError(null);
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioStream(stream);
      
      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      // Handle recording stop
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        setAudioUrl(URL.createObjectURL(audioBlob));
        setIsProcessing(false);
      };
      
      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setIsProcessing(true);
      
      // Start speech recognition if enabled
      if (autoTranscribe && voiceService.isSpeechRecognitionSupported()) {
        voiceService.startListening(
          (transcript, isFinal) => {
            if (isFinal) {
              setTranscript(prev => prev + transcript + ' ');
            }
          },
          (error) => {
            setError(error);
            if (onError) onError(error);
          },
          () => {
            if (onRecordingStart) onRecordingStart();
          },
          () => {
            // Recognition ended
          },
          language
        );
      }
      
      if (onRecordingStart) {
        onRecordingStart();
      }
    } catch (error) {
      console.error('Error starting recording:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setError(errorMessage);
      if (onError) {
        onError(`Failed to start recording: ${errorMessage}`);
      }
    }
  }, [isRecording, autoTranscribe, voiceService, onRecordingStart, onError, language]);
  
  // Cancel recording
  const cancelRecording = React.useCallback(() => {
    if (!isRecording) return;
    
    // Stop media recorder if it exists
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    // Stop speech recognition if it's active
    if (autoTranscribe && voiceService.isCurrentlyListening()) {
      voiceService.abortListening();
    }
    
    // Stop all tracks in the stream
    if (audioStream) {
      audioStream.getTracks().forEach(track => track.stop());
      setAudioStream(null);
    }
    
    // Reset state
    setIsRecording(false);
    setRecordingTime(0);
    audioChunksRef.current = [];
    setAudioBlob(null);
    setAudioUrl(null);
    setTranscript('');
    setIsProcessing(false);
    
    if (onRecordingCancel) {
      onRecordingCancel();
    }
  }, [isRecording, audioStream, autoTranscribe, voiceService, onRecordingCancel]);
  
  // Reset recording
  const resetRecording = React.useCallback(() => {
    setAudioBlob(null);
    setAudioUrl(null);
    setRecordingTime(0);
    setTranscript('');
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
  }, [audioUrl]);
  
  return {
    isRecording,
    isSupported: voiceService.isSpeechRecognitionSupported(),
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
  };
};

export default VoiceService;
