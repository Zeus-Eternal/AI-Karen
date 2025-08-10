'use client';

import React, { useState, useRef, useCallback } from 'react';
import { CopilotTextarea } from '@copilotkit/react-textarea';
import { useCopilotAction, useCopilotReadable } from '@copilotkit/react-core';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Send, 
  Mic, 
  MicOff, 
  Sparkles, 
  Code, 
  FileText, 
  Lightbulb,
  Loader2
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

interface ChatInputProps {
  onSubmit: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
  className?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSubmit,
  isLoading = false,
  placeholder = "Ask me anything...",
  className = ''
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  // CopilotKit integration - make user context available
  useCopilotReadable({
    description: "Current user information and preferences",
    value: {
      userId: user?.user_id,
      preferences: user?.preferences,
      isAuthenticated: !!user
    }
  });

  // CopilotKit action for enhanced suggestions
  useCopilotAction({
    name: "generateChatSuggestions",
    description: "Generate contextual chat suggestions based on user input",
    parameters: [
      {
        name: "context",
        type: "string",
        description: "The current input context"
      }
    ],
    handler: async ({ context }) => {
      const contextualSuggestions = [
        "Help me debug this code",
        "Explain this concept in detail",
        "Generate documentation for this",
        "What are the best practices for this?",
        "Can you optimize this approach?"
      ];
      setSuggestions(contextualSuggestions);
      return { suggestions: contextualSuggestions };
    }
  });

  // Handle form submission
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    try {
      await onSubmit(input.trim());
      setInput('');
      setSuggestions([]);
    } catch (error) {
      console.error('Failed to submit message:', error);
      toast({
        variant: 'destructive',
        title: 'Message Failed',
        description: 'Unable to send your message. Please try again.'
      });
    }
  }, [input, isLoading, onSubmit, toast]);

  // Handle voice recording
  const toggleRecording = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast({
        variant: 'destructive',
        title: 'Speech Recognition Not Supported',
        description: 'Your browser does not support speech recognition.'
      });
      return;
    }

    if (isRecording) {
      recognitionRef.current?.stop();
      setIsRecording(false);
    } else {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsRecording(true);
      };

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => prev + (prev ? ' ' : '') + transcript);
        setIsRecording(false);
      };

      recognitionRef.current.onerror = () => {
        setIsRecording(false);
        toast({
          variant: 'destructive',
          title: 'Speech Recognition Error',
          description: 'Failed to recognize speech. Please try again.'
        });
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current.start();
    }
  }, [isRecording, toast]);

  // Quick action buttons
  const quickActions = [
    {
      label: 'Debug Code',
      icon: Code,
      action: () => setInput('Help me debug this code: ')
    },
    {
      label: 'Explain',
      icon: Lightbulb,
      action: () => setInput('Please explain: ')
    },
    {
      label: 'Document',
      icon: FileText,
      action: () => setInput('Generate documentation for: ')
    }
  ];

  return (
    <Card className={`p-4 ${className}`}>
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Main Input */}
        <div className="relative">
          <CopilotTextarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={isLoading}
            className="min-h-[60px] max-h-[200px] resize-none pr-24"
            autosuggestionsConfig={{
              textareaPurpose: "Chat input for AI assistant conversation",
              chatApiConfigs: {
                suggestionsApiConfig: {
                  forwardedParams: {
                    max_tokens: 20,
                    stop: ["\n", "."]
                  }
                }
              }
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          
          {/* Voice and Send buttons */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={toggleRecording}
              disabled={isLoading}
              className={`h-8 w-8 p-0 ${isRecording ? 'text-red-500' : ''}`}
            >
              {isRecording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
            
            <Button
              type="submit"
              size="sm"
              disabled={!input.trim() || isLoading}
              className="h-8 w-8 p-0"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Sparkles className="h-3 w-3" />
            Quick actions:
          </div>
          {quickActions.map((action, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={action.action}
              disabled={isLoading}
              className="h-7 text-xs"
            >
              <action.icon className="h-3 w-3 mr-1" />
              {action.label}
            </Button>
          ))}
        </div>

        {/* Suggestions */}
        {suggestions.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">Suggestions:</div>
            <div className="flex flex-wrap gap-1">
              {suggestions.map((suggestion, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="cursor-pointer hover:bg-secondary/80 text-xs"
                  onClick={() => setInput(suggestion)}
                >
                  {suggestion}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </form>
    </Card>
  );
};

export default ChatInput;