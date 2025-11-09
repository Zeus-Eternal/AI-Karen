"use client";

import React, { forwardRef, useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Sparkles, Send, Mic, Square } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface CopilotTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  onSend?: (value: string) => void;
  onVoiceInput?: () => void;
  isRecording?: boolean;
  showCopilotSuggestions?: boolean;
  copilotEnabled?: boolean;
  containerClassName?: string;
}

const CopilotTextarea = forwardRef<HTMLTextAreaElement, CopilotTextareaProps>(
  (
    {
      onSend,
      onVoiceInput,
      isRecording = false,
      showCopilotSuggestions = false,
      copilotEnabled = true,
      containerClassName,
      className,
      value,
      onChange,
      placeholder = 'Type your message...',
      ...props
    },
    ref
  ) => {
    const [localValue, setLocalValue] = useState('');
    const textValue = value !== undefined ? value : localValue;

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (onChange) {
        onChange(e);
      } else {
        setLocalValue(e.target.value);
      }
    };

    const handleSend = () => {
      const valueToSend = String(textValue);
      if (valueToSend.trim() && onSend) {
        onSend(valueToSend);
        if (value === undefined) {
          setLocalValue('');
        }
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    };

    return (
      <div className={cn('relative', containerClassName)}>
        {copilotEnabled && showCopilotSuggestions && (
          <div className="absolute -top-12 left-0 right-0 z-10">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-start gap-2">
              <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-xs text-blue-800 dark:text-blue-200">
                  Copilot suggestion available
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Textarea
              ref={ref}
              value={textValue}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className={cn(
                'resize-none pr-24',
                className
              )}
              rows={3}
              {...props}
            />

            {copilotEnabled && (
              <div className="absolute bottom-2 right-2">
                <Sparkles className="h-4 w-4 text-gray-400" />
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2">
            {onVoiceInput && (
              <Button
                type="button"
                size="icon"
                variant={isRecording ? 'destructive' : 'outline'}
                onClick={onVoiceInput}
                title={isRecording ? 'Stop recording' : 'Start voice input'}
              >
                {isRecording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
            )}

            <Button
              type="button"
              size="icon"
              onClick={handleSend}
              disabled={!String(textValue).trim()}
              title="Send message (Enter)"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }
);

CopilotTextarea.displayName = 'CopilotTextarea';

export default CopilotTextarea;
export { CopilotTextarea };
