/**
 * Voice Control and Speech Recognition System
 * Comprehensive voice control and speech recognition for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';

// Speech Recognition types
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onstart: (event: Event) => void;
  onend: (event: Event) => void;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResultItem;
  [index: number]: SpeechRecognitionResultItem;
}

interface SpeechRecognitionResultItem {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

// Voice command interface
export interface VoiceCommand {
  id: string;
  phrases: string[];
  action: () => void;
  description: string;
  category: 'navigation' | 'interaction' | 'form' | 'accessibility' | 'custom';
  enabled: boolean;
}

// Speech recognition result
export interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

// Voice control state
export interface VoiceControlState {
  isListening: boolean;
  isSupported: boolean;
  lastCommand: string | null;
  confidence: number;
  error: string | null;
  availableCommands: VoiceCommand[];
}

// Voice control hook
export function useVoiceControl() {
  const { state, announceToScreenReader, updatePreferences } = useAccessibility();
  const [voiceState, setVoiceState] = useState<VoiceControlState>({
    isListening: false,
    isSupported: false,
    lastCommand: null,
    confidence: 0,
    error: null,
    availableCommands: [],
  });
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const commandsRef = useRef<Map<string, VoiceCommand>>(new Map());

  // Process voice command
  const processVoiceCommand = useCallback((transcript: string, confidence: number) => {
    const commands = Array.from(commandsRef.current.values());
    
    // Find matching command
    for (const command of commands) {
      if (!command.enabled) continue;
      
      for (const phrase of command.phrases) {
        if (transcript.includes(phrase.toLowerCase())) {
          announceToScreenReader(`Executing command: ${command.description}`);
          command.action();
          return;
        }
      }
    }
    
    // No command found
    if (confidence > 0.7) {
      announceToScreenReader(`Command not recognized: ${transcript}`);
    }
  }, [announceToScreenReader]);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognitionConstructor = (window as Window & { SpeechRecognition?: { new(): SpeechRecognition }; webkitSpeechRecognition?: { new(): SpeechRecognition } }).SpeechRecognition || (window as Window & { SpeechRecognition?: { new(): SpeechRecognition }; webkitSpeechRecognition?: { new(): SpeechRecognition } }).webkitSpeechRecognition;
    
    if (!SpeechRecognitionConstructor) {
      setVoiceState(prev => ({
        ...prev,
        isSupported: false,
        error: 'Speech recognition not supported in this browser',
      }));
      return;
    }

    const recognition = new SpeechRecognitionConstructor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setVoiceState(prev => ({
        ...prev,
        isListening: true,
        error: null,
      }));
      announceToScreenReader('Voice control activated');
    };

    recognition.onend = () => {
      setVoiceState(prev => ({
        ...prev,
        isListening: false,
      }));
      announceToScreenReader('Voice control deactivated');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const last = event.results.length - 1;
      const result = event.results[last];
      
      if (result && result.isFinal) {
        const alternative = result[0];
        if (alternative) {
          const transcript = alternative.transcript.toLowerCase().trim();
          const confidence = alternative.confidence;
          
          setVoiceState(prev => ({
            ...prev,
            lastCommand: transcript,
            confidence,
          }));
          
          // Process voice command
          processVoiceCommand(transcript, confidence);
        }
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      let errorMessage = 'Unknown error occurred';
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected';
          break;
        case 'audio-capture':
          errorMessage = 'Microphone not available';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone permission denied';
          break;
        case 'network':
          errorMessage = 'Network error occurred';
          break;
        case 'service-not-allowed':
          errorMessage = 'Speech recognition service not allowed';
          break;
        default:
          errorMessage = `Error: ${event.error}`;
      }
      
      setVoiceState(prev => ({
        ...prev,
        error: errorMessage,
        isListening: false,
      }));
      
      announceToScreenReader(`Voice control error: ${errorMessage}`);
    };

    recognitionRef.current = recognition;
    setVoiceState(prev => ({
      ...prev,
      isSupported: true,
    }));

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    };
  }, [announceToScreenReader, processVoiceCommand]);

  // Register default voice commands
  useEffect(() => {
    const defaultCommands: VoiceCommand[] = [
      // Navigation commands
      {
        id: 'go-home',
        phrases: ['go home', 'home', 'navigate home'],
        action: () => {
          window.location.href = '/';
        },
        description: 'Navigate to home page',
        category: 'navigation',
        enabled: true,
      },
      {
        id: 'go-back',
        phrases: ['go back', 'back', 'navigate back'],
        action: () => {
          window.history.back();
        },
        description: 'Go back to previous page',
        category: 'navigation',
        enabled: true,
      },
      {
        id: 'scroll-up',
        phrases: ['scroll up', 'page up'],
        action: () => {
          window.scrollBy({ top: -300, behavior: 'smooth' });
        },
        description: 'Scroll up the page',
        category: 'navigation',
        enabled: true,
      },
      {
        id: 'scroll-down',
        phrases: ['scroll down', 'page down'],
        action: () => {
          window.scrollBy({ top: 300, behavior: 'smooth' });
        },
        description: 'Scroll down the page',
        category: 'navigation',
        enabled: true,
      },
      
      // Interaction commands
      {
        id: 'click-button',
        phrases: ['click button', 'press button', 'activate button'],
        action: () => {
          const focusedElement = document.activeElement as HTMLElement;
          if (focusedElement && (focusedElement.tagName === 'BUTTON' || focusedElement.getAttribute('role') === 'button')) {
            focusedElement.click();
            announceToScreenReader('Button clicked');
          } else {
            announceToScreenReader('No button focused');
          }
        },
        description: 'Click the focused button',
        category: 'interaction',
        enabled: true,
      },
      {
        id: 'open-link',
        phrases: ['open link', 'follow link', 'go to link'],
        action: () => {
          const focusedElement = document.activeElement as HTMLElement;
          if (focusedElement && (focusedElement.tagName === 'A' || focusedElement.getAttribute('role') === 'link')) {
            (focusedElement as HTMLAnchorElement).click();
            announceToScreenReader('Link opened');
          } else {
            announceToScreenReader('No link focused');
          }
        },
        description: 'Open the focused link',
        category: 'interaction',
        enabled: true,
      },
      
      // Form commands
      {
        id: 'focus-input',
        phrases: ['focus input', 'select input', 'edit field'],
        action: () => {
          const inputs = document.querySelectorAll('input, textarea, select') as NodeListOf<HTMLElement>;
          if (inputs.length > 0) {
            inputs[0]?.focus();
            announceToScreenReader('Focused on first input field');
          } else {
            announceToScreenReader('No input fields found');
          }
        },
        description: 'Focus on the first input field',
        category: 'form',
        enabled: true,
      },
      {
        id: 'submit-form',
        phrases: ['submit form', 'send form', 'save form'],
        action: () => {
          const focusedElement = document.activeElement as HTMLElement;
          if (focusedElement && (focusedElement as HTMLInputElement).form) {
            (focusedElement as HTMLInputElement).form?.submit();
            announceToScreenReader('Form submitted');
          } else {
            const submitButton = document.querySelector('button[type="submit"], input[type="submit"]') as HTMLElement;
            if (submitButton) {
              submitButton.click();
              announceToScreenReader('Form submitted');
            } else {
              announceToScreenReader('No form to submit');
            }
          }
        },
        description: 'Submit the current form',
        category: 'form',
        enabled: true,
      },
      
      // Accessibility commands
      {
        id: 'toggle-high-contrast',
        phrases: ['toggle high contrast', 'high contrast on', 'high contrast off'],
        action: () => {
          updatePreferences({ highContrast: !state.preferences.highContrast });
        },
        description: 'Toggle high contrast mode',
        category: 'accessibility',
        enabled: true,
      },
      {
        id: 'toggle-large-text',
        phrases: ['toggle large text', 'large text on', 'large text off'],
        action: () => {
          updatePreferences({ largeText: !state.preferences.largeText });
        },
        description: 'Toggle large text mode',
        category: 'accessibility',
        enabled: true,
      },
      {
        id: 'toggle-reduced-motion',
        phrases: ['toggle reduced motion', 'reduced motion on', 'reduced motion off'],
        action: () => {
          updatePreferences({ reducedMotion: !state.preferences.reducedMotion });
        },
        description: 'Toggle reduced motion',
        category: 'accessibility',
        enabled: true,
      },
      {
        id: 'voice-help',
        phrases: ['voice help', 'help commands', 'what can i say'],
        action: () => {
          const enabledCommands = Array.from(commandsRef.current.values()).filter(cmd => cmd.enabled);
          const commandList = enabledCommands.map(cmd => cmd.description).join(', ');
          announceToScreenReader(`Available voice commands: ${commandList}`);
        },
        description: 'List available voice commands',
        category: 'accessibility',
        enabled: true,
      },
    ];

    // Register commands
    defaultCommands.forEach(command => {
      commandsRef.current.set(command.id, command);
    });

    setVoiceState(prev => ({
      ...prev,
      availableCommands: defaultCommands,
    }));
  }, [state.preferences, updatePreferences, announceToScreenReader]);

  // Start voice recognition
  const startListening = useCallback(() => {
    if (!recognitionRef.current || !voiceState.isSupported) return;
    
    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      setVoiceState(prev => ({
        ...prev,
        error: 'Failed to start voice recognition',
      }));
    }
  }, [voiceState.isSupported]);

  // Stop voice recognition
  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    
    recognitionRef.current.stop();
  }, []);

  // Toggle voice recognition
  const toggleListening = useCallback(() => {
    if (voiceState.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [voiceState.isListening, startListening, stopListening]);

  // Add custom voice command
  const addCommand = useCallback((command: VoiceCommand) => {
    commandsRef.current.set(command.id, command);
    setVoiceState(prev => ({
      ...prev,
      availableCommands: Array.from(commandsRef.current.values()),
    }));
  }, []);

  // Remove voice command
  const removeCommand = useCallback((commandId: string) => {
    commandsRef.current.delete(commandId);
    setVoiceState(prev => ({
      ...prev,
      availableCommands: Array.from(commandsRef.current.values()),
    }));
  }, []);

  // Enable/disable command
  const toggleCommand = useCallback((commandId: string, enabled: boolean) => {
    const command = commandsRef.current.get(commandId);
    if (command) {
      command.enabled = enabled;
      setVoiceState(prev => ({
        ...prev,
        availableCommands: Array.from(commandsRef.current.values()),
      }));
    }
  }, []);

  // Text-to-speech for feedback
  const speak = useCallback((text: string, options: {
    rate?: number;
    pitch?: number;
    volume?: number;
    lang?: string;
  } = {}) => {
    if (!('speechSynthesis' in window)) return;

    const { rate = 1, pitch = 1, volume = 1, lang = 'en-US' } = options;
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = volume;
    utterance.lang = lang;
    
    window.speechSynthesis.speak(utterance);
  }, []);

  return {
    voiceState,
    startListening,
    stopListening,
    toggleListening,
    addCommand,
    removeCommand,
    toggleCommand,
    speak,
  };
}

// Voice control component
export interface VoiceControlProps {
  className?: string;
  showCommands?: boolean;
}

export function VoiceControl({ className = '', showCommands = true }: VoiceControlProps) {
  const { voiceState, toggleListening, removeCommand, toggleCommand } = useVoiceControl();

  return React.createElement('div', {
    className: `voice-control ${className}`,
    role: 'region',
    'aria-label': 'Voice control interface',
  }, [
    React.createElement('div', { key: 'controls', className: 'voice-controls' }, [
      React.createElement('button', {
        key: 'toggle',
        onClick: toggleListening,
        className: `voice-toggle ${voiceState.isListening ? 'listening' : ''}`,
        'aria-pressed': voiceState.isListening,
        'aria-label': voiceState.isListening ? 'Stop voice control' : 'Start voice control',
      }, [
        React.createElement('span', { key: 'icon', className: 'voice-icon' },
          voiceState.isListening ? '🎤' : '🎙️'
        ),
        React.createElement('span', { key: 'text', className: 'voice-text' },
          voiceState.isListening ? 'Listening...' : 'Voice Control'
        ),
      ]),
      
      voiceState.error && React.createElement('div', {
        key: 'error',
        className: 'voice-error',
        role: 'alert',
        'aria-live': 'polite',
      }, voiceState.error),
    ]),
    
    showCommands && React.createElement('div', { key: 'commands', className: 'voice-commands' }, [
      React.createElement('h3', { key: 'title' }, 'Voice Commands'),
      React.createElement('ul', { key: 'list', className: 'command-list' },
        voiceState.availableCommands.map(command =>
          React.createElement('li', {
            key: command.id,
            className: `command-item ${command.enabled ? 'enabled' : 'disabled'}`,
          }, [
            React.createElement('div', { key: 'info', className: 'command-info' }, [
              React.createElement('span', { key: 'description', className: 'command-description' },
                command.description
              ),
              React.createElement('span', { key: 'category', className: 'command-category' },
                command.category
              ),
            ]),
            React.createElement('div', { key: 'phrases', className: 'command-phrases' },
              command.phrases.map((phrase, index) =>
                React.createElement('code', { key: index }, `"${phrase}"`)
              )
            ),
            React.createElement('div', { key: 'actions', className: 'command-actions' }, [
              React.createElement('button', {
                key: 'toggle',
                onClick: () => toggleCommand(command.id, !command.enabled),
                className: 'command-toggle',
                'aria-label': `${command.enabled ? 'Disable' : 'Enable'} command: ${command.description}`,
              }, command.enabled ? 'Disable' : 'Enable'),
              React.createElement('button', {
                key: 'remove',
                onClick: () => removeCommand(command.id),
                className: 'command-remove',
                'aria-label': `Remove command: ${command.description}`,
              }, 'Remove'),
            ]),
          ])
        )
      ),
    ]),
  ]);
}

// Custom voice command creator component
export interface VoiceCommandCreatorProps {
  onCommandCreate: (command: VoiceCommand) => void;
  className?: string;
}

export function VoiceCommandCreator({ onCommandCreate, className = '' }: VoiceCommandCreatorProps) {
  const [formData, setFormData] = useState({
    description: '',
    phrases: '',
    category: 'custom' as VoiceCommand['category'],
  });
  const { addCommand } = useVoiceControl();

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.description || !formData.phrases) return;
    
    const command: VoiceCommand = {
      id: `custom-${Date.now()}`,
      description: formData.description,
      phrases: formData.phrases.split(',').map(p => p.trim()),
      category: formData.category,
      action: () => {
        // Custom action would be defined by user
        console.log(`Custom command executed: ${formData.description}`);
      },
      enabled: true,
    };
    
    addCommand(command);
    onCommandCreate(command);
    
    // Reset form
    setFormData({
      description: '',
      phrases: '',
      category: 'custom',
    });
  }, [formData, addCommand, onCommandCreate]);

  return React.createElement('form', {
    className: `voice-command-creator ${className}`,
    onSubmit: handleSubmit,
    'aria-label': 'Create custom voice command',
  }, [
    React.createElement('h3', { key: 'title' }, 'Create Custom Voice Command'),
    
    React.createElement('div', { key: 'description', className: 'form-group' },
      React.createElement('label', { htmlFor: 'command-description' }, 'Command Description'),
      React.createElement('input', {
        id: 'command-description',
        type: 'text',
        value: formData.description,
        onChange: (e: React.ChangeEvent<HTMLInputElement>) => setFormData(prev => ({
          ...prev,
          description: e.target.value,
        })),
        required: true,
        'aria-describedby': 'command-description-help',
      }),
      React.createElement('span', {
        key: 'help',
        id: 'command-description-help',
        className: 'form-help',
      }, 'Describe what the command does')
    ),
    
    React.createElement('div', { key: 'phrases', className: 'form-group' },
      React.createElement('label', { htmlFor: 'command-phrases' }, 'Voice Phrases'),
      React.createElement('textarea', {
        id: 'command-phrases',
        value: formData.phrases,
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({
          ...prev,
          phrases: e.target.value,
        })),
        required: true,
        'aria-describedby': 'command-phrases-help',
        rows: 3,
      }),
      React.createElement('span', {
        key: 'help',
        id: 'command-phrases-help',
        className: 'form-help',
      }, 'Enter phrases separated by commas (e.g., "open menu, show menu, display menu")')
    ),
    
    React.createElement('div', { key: 'category', className: 'form-group' },
      React.createElement('label', { htmlFor: 'command-category' }, 'Category'),
      React.createElement('select', {
        id: 'command-category',
        value: formData.category,
        onChange: (e: React.ChangeEvent<HTMLSelectElement>) => setFormData(prev => ({
          ...prev,
          category: e.target.value as VoiceCommand['category'],
        })),
      }, [
        React.createElement('option', { key: 'navigation', value: 'navigation' }, 'Navigation'),
        React.createElement('option', { key: 'interaction', value: 'interaction' }, 'Interaction'),
        React.createElement('option', { key: 'form', value: 'form' }, 'Form'),
        React.createElement('option', { key: 'accessibility', value: 'accessibility' }, 'Accessibility'),
        React.createElement('option', { key: 'custom', value: 'custom' }, 'Custom'),
      ])
    ),
    
    React.createElement('div', { key: 'actions', className: 'form-actions' },
      React.createElement('button', {
        type: 'submit',
        className: 'create-button',
        disabled: !formData.description || !formData.phrases,
      }, 'Create Command')
    ),
  ]);
}
