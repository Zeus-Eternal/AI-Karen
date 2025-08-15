# Path: ui_launchers/web_ui/src/components/chat/Composer.tsx

'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Send, 
  Mic, 
  MicOff, 
  Paperclip, 
  Smile, 
  Loader2,
  AlertTriangle,
  Zap,
  Code,
  FileText,
  Lightbulb
} from 'lucide-react';
import { useFeature } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';
import { useVoiceInput } from '@/hooks/use-voice-input';
import { useKeyboardNavigation, createChatKeyboardShortcuts } from '@/hooks/use-keyboard-navigation';
import { RBACGuard } from '@/components/security/RBACGuard';

interface ComposerProps {
  onSubmit: (message: string, type?: MessageType) => Promise<void>;
  isDisabled?: boolean;
  placeholder?: string;
  maxLength?: number;
  className?: string;
  features?: ComposerFeatures;
  onAbort?: () => void;
  onClear?: () => void;
  autoFocus?: boolean;
}

interface ComposerFeatures {
  voice?: boolean;
  attachments?: boolean;
  quickActions?: boolean;
  emoji?: boolean;
}

type MessageType = 'text' | 'code' | 'command';

const MAX_LENGTH = 4000;
const WARNING_THRESHOLD = 3500;

const quickActions = [
  { 
    icon: Code, 
    label: 'Debug Code', 
    prompt: 'Help me debug this code: ',
    type: 'code' as MessageType,
    permission: 'chat.code_assistance'
  },
  { 
    icon: Lightbulb, 
    label: 'Explain', 
    prompt: 'Please explain: ',
    type: 'text' as MessageType,
    permission: 'chat.explanations'
  },
  { 
    icon: FileText, 
    label: 'Document', 
    prompt: 'Generate documentation for: ',
    type: 'text' as MessageType,
    permission: 'chat.documentation'
  },
  { 
    icon: Zap, 
    label: 'Analyze', 
    prompt: 'Please analyze: ',
    type: 'text' as MessageType,
    permission: 'chat.analysis'
  }
];

export const Composer: React.FC<ComposerProps> = ({
  onSubmit,
  isDisabled = false,
  placeholder = "Type your message...",
  maxLength = MAX_LENGTH,
  className = '',
  features = {},
  onAbort,
  onClear,
  autoFocus = false
}) => {
  const [input, setInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuickActionIndex, setSelectedQuickActionIndex] = useState(-1);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const composerRef = useRef<HTMLDivElement>(null);
  const { track } = useTelemetry();
  
  // Feature flags
  const voiceEnabled = useFeature('voice.input') && features.voice;
  const attachmentsEnabled = useFeature('attachments.enabled') && features.attachments;
  const quickActionsEnabled = useFeature('chat.quick_actions') && features.quickActions;
  const emojiEnabled = useFeature('emoji.picker') && features.emoji;
  
  // Voice input hook
  const {
    isRecording,
    isSupported: voiceSupported,
    startRecording,
    stopRecording,
    transcript
  } = useVoiceInput({
    onTranscript: (text) => {
      setInput(prev => prev + (prev ? ' ' : '') + text);
      track('voice_input_used', { transcriptLength: text.length });
    },
    onError: (error) => {
      setError(`Voice input error: ${error.message}`);
      track('voice_input_error', { error: error.message });
    }
  });

  // Focus management
  const focusInput = useCallback(() => {
    textareaRef.current?.focus();
  }, []);

  // Clear input and focus
  const clearInput = useCallback(() => {
    setInput('');
    setError(null);
    setSelectedQuickActionIndex(-1);
    focusInput();
    track('composer_input_cleared');
  }, [focusInput, track]);

  // Keyboard shortcuts
  const keyboardShortcuts = createChatKeyboardShortcuts({
    onSend: () => handleSubmit(),
    onAbort: onAbort,
    onClear: onClear || clearInput,
    onFocusInput: focusInput,
    onToggleVoice: voiceEnabled && voiceSupported ? handleVoiceToggle : undefined
  });

  // Keyboard navigation
  const { containerRef } = useKeyboardNavigation({
    shortcuts: keyboardShortcuts,
    autoFocus: autoFocus,
    onEscape: () => {
      if (isRecording) {
        stopRecording();
      } else if (input.trim()) {
        clearInput();
      } else {
        onAbort?.();
      }
    },
    onEnter: () => {
      if (selectedQuickActionIndex >= 0) {
        handleQuickAction(quickActions[selectedQuickActionIndex]);
      } else {
        handleSubmit();
      }
    }
  });

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Handle form submission
  const handleSubmit = useCallback(async (messageType: MessageType = 'text') => {
    if (!input.trim() || isSubmitting || isDisabled) return;

    const message = input.trim();
    setIsSubmitting(true);
    setError(null);

    try {
      track('message_compose_submit', {
        messageLength: message.length,
        messageType,
        hasQuickAction: quickActions.some(action => message.startsWith(action.prompt))
      });

      await onSubmit(message, messageType);
      setInput('');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      track('message_compose_error', { error: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  }, [input, isSubmitting, isDisabled, onSubmit, track]);

  // Enhanced keyboard handling for textarea
  const handleTextareaKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    const { key, shiftKey, ctrlKey, altKey } = e;

    // Handle Enter key
    if (key === 'Enter' && !shiftKey) {
      e.preventDefault();
      if (selectedQuickActionIndex >= 0) {
        handleQuickAction(quickActions[selectedQuickActionIndex]);
      } else {
        handleSubmit();
      }
      return;
    }

    // Handle Escape key
    if (key === 'Escape') {
      e.preventDefault();
      if (isRecording) {
        stopRecording();
      } else if (input.trim()) {
        clearInput();
      } else {
        textareaRef.current?.blur();
        onAbort?.();
      }
      return;
    }

    // Handle quick action navigation with arrow keys
    if (quickActionsEnabled && (key === 'ArrowUp' || key === 'ArrowDown') && ctrlKey) {
      e.preventDefault();
      const maxIndex = quickActions.length - 1;
      
      if (key === 'ArrowDown') {
        setSelectedQuickActionIndex(prev => 
          prev < maxIndex ? prev + 1 : 0
        );
      } else {
        setSelectedQuickActionIndex(prev => 
          prev > 0 ? prev - 1 : maxIndex
        );
      }
      track('quick_action_navigation', { direction: key === 'ArrowDown' ? 'down' : 'up' });
      return;
    }

    // Handle Tab for quick actions
    if (key === 'Tab' && quickActionsEnabled && !shiftKey && ctrlKey) {
      e.preventDefault();
      setSelectedQuickActionIndex(prev => 
        prev < quickActions.length - 1 ? prev + 1 : -1
      );
      return;
    }

    // Handle voice toggle shortcut
    if (key === 'm' && ctrlKey && voiceEnabled && voiceSupported) {
      e.preventDefault();
      handleVoiceToggle();
      return;
    }

    // Clear selection when typing
    if (selectedQuickActionIndex >= 0 && key.length === 1) {
      setSelectedQuickActionIndex(-1);
    }
  }, [
    handleSubmit, 
    handleQuickAction, 
    quickActions, 
    selectedQuickActionIndex,
    quickActionsEnabled,
    isRecording,
    stopRecording,
    clearInput,
    onAbort,
    input,
    voiceEnabled,
    voiceSupported,
    handleVoiceToggle,
    track
  ]);

  // Handle quick action selection
  const handleQuickAction = useCallback((action: typeof quickActions[0]) => {
    setInput(action.prompt);
    textareaRef.current?.focus();
    track('quick_action_used', { action: action.label });
  }, [track]);

  // Handle voice toggle
  const handleVoiceToggle = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
    track('voice_toggle', { isRecording: !isRecording });
  }, [isRecording, startRecording, stopRecording, track]);

  // Input validation
  const isOverLimit = input.length > maxLength;
  const isNearLimit = input.length > WARNING_THRESHOLD;
  const canSubmit = input.trim() && !isSubmitting && !isDisabled && !isOverLimit;

  // Sync container refs
  useEffect(() => {
    if (composerRef.current) {
      containerRef.current = composerRef.current;
    }
  }, [containerRef]);

  return (
    <div 
      ref={composerRef}
      className={`border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 ${className}`}
      role="region"
      aria-label="Message composer"
    >
      <div className="container max-w-4xl mx-auto p-4">
        {/* Quick Actions */}
        {quickActionsEnabled && (
          <div 
            className="flex items-center gap-2 mb-3 overflow-x-auto pb-2"
            role="toolbar"
            aria-label="Quick actions"
          >
            <span className="text-xs text-muted-foreground whitespace-nowrap">Quick actions:</span>
            {quickActions.map((action, index) => (
              <RBACGuard key={index} permission={action.permission} fallback={null}>
                <Button
                  variant={selectedQuickActionIndex === index ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleQuickAction(action)}
                  disabled={isDisabled || isSubmitting}
                  className={`flex items-center gap-1.5 text-xs whitespace-nowrap ${
                    selectedQuickActionIndex === index ? 'ring-2 ring-primary' : ''
                  }`}
                  aria-pressed={selectedQuickActionIndex === index}
                  aria-describedby={`quick-action-${index}-desc`}
                >
                  <action.icon className="h-3 w-3" />
                  {action.label}
                  <span id={`quick-action-${index}-desc`} className="sr-only">
                    {action.prompt}
                  </span>
                </Button>
              </RBACGuard>
            ))}
          </div>
        )}

        {/* Main Input Area */}
        <div className="relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleTextareaKeyDown}
            placeholder={placeholder}
            disabled={isDisabled || isSubmitting}
            maxLength={maxLength}
            className={`min-h-[60px] max-h-[200px] resize-none pr-20 ${
              isOverLimit ? 'border-destructive focus-visible:ring-destructive' : ''
            }`}
            aria-label="Message input"
            aria-describedby={[
              error ? 'composer-error' : '',
              'composer-help',
              selectedQuickActionIndex >= 0 ? `quick-action-${selectedQuickActionIndex}-desc` : ''
            ].filter(Boolean).join(' ')}
            aria-invalid={isOverLimit}
            autoFocus={autoFocus}
          />

          {/* Action Buttons */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            {/* Voice Input */}
            {voiceEnabled && voiceSupported && (
              <RBACGuard permission="voice.input" fallback={null}>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleVoiceToggle}
                  disabled={isDisabled || isSubmitting}
                  className={`h-8 w-8 p-0 ${isRecording ? 'text-red-500 animate-pulse' : ''}`}
                  aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
                >
                  {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </Button>
              </RBACGuard>
            )}

            {/* Attachments */}
            {attachmentsEnabled && (
              <RBACGuard permission="attachments.upload" fallback={null}>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={isDisabled || isSubmitting}
                  className="h-8 w-8 p-0"
                  aria-label="Attach file"
                >
                  <Paperclip className="h-4 w-4" />
                </Button>
              </RBACGuard>
            )}

            {/* Emoji Picker */}
            {emojiEnabled && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled={isDisabled || isSubmitting}
                className="h-8 w-8 p-0"
                aria-label="Add emoji"
              >
                <Smile className="h-4 w-4" />
              </Button>
            )}

            {/* Send Button */}
            <Button
              type="submit"
              size="sm"
              onClick={() => handleSubmit()}
              disabled={!canSubmit}
              className={`h-8 w-8 p-0 ${
                canSubmit 
                  ? 'bg-primary hover:bg-primary/90' 
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
              }`}
              aria-label="Send message"
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="flex items-center justify-between mt-2 text-xs">
          <div className="flex items-center gap-2">
            {error && (
              <div id="composer-error" className="flex items-center gap-1 text-destructive">
                <AlertTriangle className="h-3 w-3" />
                <span>{error}</span>
              </div>
            )}
            
            {isRecording && (
              <Badge variant="destructive" className="animate-pulse">
                Recording...
              </Badge>
            )}
          </div>

          <div className={`${
            isOverLimit 
              ? 'text-destructive' 
              : isNearLimit 
              ? 'text-warning' 
              : 'text-muted-foreground'
          }`}>
            {input.length}/{maxLength}
          </div>
        </div>

        {/* Help Text */}
        <div id="composer-help" className="text-xs text-muted-foreground text-center mt-2">
          <div className="flex flex-wrap justify-center gap-x-4 gap-y-1">
            <span>
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Enter</kbd> to send
            </span>
            <span>
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Shift+Enter</kbd> for new line
            </span>
            <span>
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Esc</kbd> to clear
            </span>
            {quickActionsEnabled && (
              <>
                <span>
                  <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Ctrl+↑/↓</kbd> navigate actions
                </span>
                <span>
                  <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Ctrl+Tab</kbd> select action
                </span>
              </>
            )}
            {voiceEnabled && voiceSupported && (
              <span>
                <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Ctrl+M</kbd> toggle voice
              </span>
            )}
          </div>
          {selectedQuickActionIndex >= 0 && (
            <div className="mt-1 text-primary">
              Selected: {quickActions[selectedQuickActionIndex].label}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Composer;