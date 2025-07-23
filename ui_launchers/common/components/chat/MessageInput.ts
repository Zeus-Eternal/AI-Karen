// Shared Message Input Component
// Framework-agnostic message input with voice support

import { Theme } from '../../abstractions/types';
import { validator, errorHandler, debounce } from '../../abstractions/utils';

export interface MessageInputOptions {
  placeholder?: string;
  maxLength?: number;
  enableVoice?: boolean;
  enableAttachments?: boolean;
  multiline?: boolean;
  autoFocus?: boolean;
  showCharacterCount?: boolean;
  submitOnEnter?: boolean;
  enableSuggestions?: boolean;
}

export interface MessageInputState {
  value: string;
  isRecording: boolean;
  isLoading: boolean;
  hasError: boolean;
  errorMessage: string;
  characterCount: number;
  suggestions: string[];
  showSuggestions: boolean;
}

export interface MessageInputCallbacks {
  onSubmit?: (message: string, isVoice?: boolean) => void;
  onChange?: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
  onSuggestionSelect?: (suggestion: string) => void;
}

export class SharedMessageInput {
  private state: MessageInputState;
  private options: MessageInputOptions;
  private callbacks: MessageInputCallbacks;
  private theme: Theme;
  private debouncedOnChange: (value: string) => void;

  constructor(
    theme: Theme,
    options: MessageInputOptions = {},
    callbacks: MessageInputCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      placeholder: 'Type your message...',
      maxLength: 10000,
      enableVoice: true,
      enableAttachments: false,
      multiline: false,
      autoFocus: false,
      showCharacterCount: false,
      submitOnEnter: true,
      enableSuggestions: false,
      ...options
    };
    this.callbacks = callbacks;

    this.state = {
      value: '',
      isRecording: false,
      isLoading: false,
      hasError: false,
      errorMessage: '',
      characterCount: 0,
      suggestions: [],
      showSuggestions: false
    };

    // Create debounced onChange handler
    this.debouncedOnChange = debounce((value: string) => {
      if (this.callbacks.onChange) {
        this.callbacks.onChange(value);
      }
    }, 300);
  }

  // Get current state
  getState(): MessageInputState {
    return { ...this.state };
  }

  // Update state
  updateState(newState: Partial<MessageInputState>): void {
    this.state = { ...this.state, ...newState };
  }

  // Get CSS classes
  getCssClasses(): string[] {
    const classes = ['karen-message-input'];
    
    if (this.state.hasError) {
      classes.push('karen-message-input-error');
    }
    
    if (this.state.isLoading) {
      classes.push('karen-message-input-loading');
    }
    
    if (this.state.isRecording) {
      classes.push('karen-message-input-recording');
    }
    
    if (this.options.multiline) {
      classes.push('karen-message-input-multiline');
    }
    
    return classes;
  }

  // Get inline styles
  getInlineStyles(): Record<string, string> {
    return {
      backgroundColor: this.theme.colors.surface,
      color: this.theme.colors.text,
      border: `1px solid ${this.state.hasError ? this.theme.colors.error : this.theme.colors.border}`,
      borderRadius: this.theme.borderRadius,
      padding: this.theme.spacing.sm,
      fontFamily: this.theme.typography.fontFamily,
      fontSize: this.theme.typography.fontSize.base,
      outline: 'none',
      transition: 'border-color 0.2s ease'
    };
  }

  // Handle input change
  handleChange(value: string): void {
    // Validate length
    if (this.options.maxLength && value.length > this.options.maxLength) {
      this.updateState({
        hasError: true,
        errorMessage: `Message too long (${value.length}/${this.options.maxLength} characters)`
      });
      return;
    }

    // Clear error if value is valid
    if (this.state.hasError && value.length <= (this.options.maxLength || Infinity)) {
      this.updateState({
        hasError: false,
        errorMessage: ''
      });
    }

    // Update state
    this.updateState({
      value,
      characterCount: value.length
    });

    // Call debounced onChange
    this.debouncedOnChange(value);

    // Handle suggestions
    if (this.options.enableSuggestions) {
      this.updateSuggestions(value);
    }
  }

  // Handle form submission
  handleSubmit(): void {
    const message = this.state.value.trim();
    
    if (!message) {
      this.updateState({
        hasError: true,
        errorMessage: 'Please enter a message'
      });
      return;
    }

    // Validate message
    const errors = validator.validateChatMessage({
      content: message,
      role: 'user',
      timestamp: new Date()
    });

    if (errors.length > 0) {
      this.updateState({
        hasError: true,
        errorMessage: errors[0]
      });
      return;
    }

    // Clear input and call callback
    this.updateState({
      value: '',
      characterCount: 0,
      hasError: false,
      errorMessage: '',
      showSuggestions: false
    });

    if (this.callbacks.onSubmit) {
      this.callbacks.onSubmit(message, false);
    }
  }

  // Handle key press
  handleKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter') {
      if (this.options.submitOnEnter && !event.shiftKey) {
        event.preventDefault();
        this.handleSubmit();
      }
    }
  }

  // Handle focus
  handleFocus(): void {
    if (this.callbacks.onFocus) {
      this.callbacks.onFocus();
    }
  }

  // Handle blur
  handleBlur(): void {
    // Hide suggestions after a delay to allow for selection
    setTimeout(() => {
      this.updateState({ showSuggestions: false });
    }, 200);

    if (this.callbacks.onBlur) {
      this.callbacks.onBlur();
    }
  }

  // Handle voice recording
  async handleVoiceToggle(): Promise<void> {
    if (!this.options.enableVoice) {
      errorHandler.showUserWarning('Voice input is not enabled');
      return;
    }

    if (this.state.isRecording) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  // Start voice recording
  private async startRecording(): Promise<void> {
    try {
      this.updateState({ isRecording: true });
      
      if (this.callbacks.onRecordingStart) {
        this.callbacks.onRecordingStart();
      }
    } catch (error) {
      errorHandler.handleError(error as Error, 'start recording');
      this.updateState({ isRecording: false });
    }
  }

  // Stop voice recording
  private stopRecording(): void {
    this.updateState({ isRecording: false });
    
    if (this.callbacks.onRecordingStop) {
      this.callbacks.onRecordingStop();
    }
  }

  // Handle voice input result
  handleVoiceResult(transcript: string): void {
    this.updateState({
      value: transcript,
      characterCount: transcript.length,
      isRecording: false
    });

    // Auto-submit voice input
    if (transcript.trim() && this.callbacks.onSubmit) {
      this.callbacks.onSubmit(transcript.trim(), true);
      this.updateState({
        value: '',
        characterCount: 0
      });
    }
  }

  // Update suggestions based on input
  private updateSuggestions(value: string): void {
    if (!value.trim()) {
      this.updateState({
        suggestions: [],
        showSuggestions: false
      });
      return;
    }

    // This would typically call an API for suggestions
    // For now, we'll use some basic suggestions
    const basicSuggestions = [
      'What can you help me with?',
      'Tell me about...',
      'How do I...',
      'What is...',
      'Can you explain...'
    ];

    const filteredSuggestions = basicSuggestions.filter(suggestion =>
      suggestion.toLowerCase().includes(value.toLowerCase())
    );

    this.updateState({
      suggestions: filteredSuggestions.slice(0, 5),
      showSuggestions: filteredSuggestions.length > 0
    });
  }

  // Handle suggestion selection
  handleSuggestionSelect(suggestion: string): void {
    this.updateState({
      value: suggestion,
      characterCount: suggestion.length,
      showSuggestions: false
    });

    if (this.callbacks.onSuggestionSelect) {
      this.callbacks.onSuggestionSelect(suggestion);
    }
  }

  // Get render data for framework implementation
  getRenderData(): MessageInputRenderData {
    return {
      state: this.getState(),
      options: this.options,
      cssClasses: this.getCssClasses(),
      styles: this.getInlineStyles(),
      theme: this.theme,
      handlers: {
        onChange: (value: string) => this.handleChange(value),
        onSubmit: () => this.handleSubmit(),
        onKeyPress: (event: KeyboardEvent) => this.handleKeyPress(event),
        onFocus: () => this.handleFocus(),
        onBlur: () => this.handleBlur(),
        onVoiceToggle: () => this.handleVoiceToggle(),
        onSuggestionSelect: (suggestion: string) => this.handleSuggestionSelect(suggestion)
      }
    };
  }

  // Update theme
  updateTheme(theme: Theme): void {
    this.theme = theme;
  }

  // Clear input
  clear(): void {
    this.updateState({
      value: '',
      characterCount: 0,
      hasError: false,
      errorMessage: '',
      showSuggestions: false
    });
  }

  // Set loading state
  setLoading(loading: boolean): void {
    this.updateState({ isLoading: loading });
  }

  // Set error state
  setError(error: string): void {
    this.updateState({
      hasError: !!error,
      errorMessage: error
    });
  }

  // Get validation status
  isValid(): boolean {
    const message = this.state.value.trim();
    
    if (!message) return false;
    if (this.options.maxLength && message.length > this.options.maxLength) return false;
    
    const errors = validator.validateChatMessage({
      content: message,
      role: 'user',
      timestamp: new Date()
    });
    
    return errors.length === 0;
  }
}

// Supporting interfaces
export interface MessageInputRenderData {
  state: MessageInputState;
  options: MessageInputOptions;
  cssClasses: string[];
  styles: Record<string, string>;
  theme: Theme;
  handlers: {
    onChange: (value: string) => void;
    onSubmit: () => void;
    onKeyPress: (event: KeyboardEvent) => void;
    onFocus: () => void;
    onBlur: () => void;
    onVoiceToggle: () => void;
    onSuggestionSelect: (suggestion: string) => void;
  };
}

// Utility functions
export function createMessageInput(
  theme: Theme,
  options: MessageInputOptions = {},
  callbacks: MessageInputCallbacks = {}
): SharedMessageInput {
  return new SharedMessageInput(theme, options, callbacks);
}

export function getInputPlaceholder(isRecording: boolean, enableVoice: boolean): string {
  if (isRecording) {
    return 'Listening...';
  }
  
  if (enableVoice) {
    return 'Type your message or use voice input...';
  }
  
  return 'Type your message...';
}

export function formatCharacterCount(current: number, max?: number): string {
  if (!max) return `${current}`;
  
  const percentage = (current / max) * 100;
  const className = percentage > 90 ? 'warning' : percentage > 75 ? 'caution' : 'normal';
  
  return `${current}/${max}`;
}

export function getVoiceButtonLabel(isRecording: boolean, isSupported: boolean): string {
  if (!isSupported) return 'Voice input not supported';
  if (isRecording) return 'Stop recording';
  return 'Start voice input';
}

export function shouldShowSubmitButton(value: string, isLoading: boolean): boolean {
  return value.trim().length > 0 && !isLoading;
}