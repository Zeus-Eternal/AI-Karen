'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { CopilotChat as CopilotKitChat } from '@copilotkit/react-ui';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Bot, Code, FileText, Lightbulb, Loader2, Sparkles } from 'lucide-react';
import { useCopilotKit } from './CopilotKitProvider';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { ChatBubble } from '@/components/chat/ChatBubble';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'text' | 'code' | 'suggestion' | 'analysis';
  language?: string;
  metadata?: {
    confidence?: number;
    sources?: string[];
    reasoning?: string;
  };
}

interface CopilotChatProps {
  initialMessages?: ChatMessage[];
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;
  enableCodeAssistance?: boolean;
  enableContextualHelp?: boolean;
  className?: string;
  height?: string;
}

export const CopilotChat: React.FC<CopilotChatProps> = ({
  initialMessages = [],
  onMessageSent,
  onMessageReceived,
  enableCodeAssistance = true,
  enableContextualHelp = true,
  className = '',
  height = '600px'
}) => {
  const { user } = useAuth();
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const { config, isLoading, getSuggestions } = useCopilotKit();
  
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentContext, setCurrentContext] = useState<string>('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Send message
  const sendMessage = useCallback(async (content: string, type: ChatMessage['type'] = 'text') => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      type
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Trigger hook for message sent
    await triggerHooks('copilot_message_sent', {
      messageId: userMessage.id,
      content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
      type,
      userId: user?.user_id
    }, { userId: user?.user_id });

    if (onMessageSent) {
      onMessageSent(userMessage);
    }

    try {
      // Simulate AI response (in real implementation, this would call the CopilotKit API)
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: await generateAIResponse(content, type),
        timestamp: new Date(),
        type: type === 'code' ? 'code' : 'text',
        metadata: {
          confidence: 0.85 + Math.random() * 0.1,
          sources: ['CopilotKit AI', 'Knowledge Base'],
          reasoning: 'Generated based on context and user query'
        }
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Trigger hook for message received
      await triggerHooks('copilot_message_received', {
        messageId: assistantMessage.id,
        confidence: assistantMessage.metadata?.confidence,
        type: assistantMessage.type,
        userId: user?.user_id
      }, { userId: user?.user_id });

      if (onMessageReceived) {
        onMessageReceived(assistantMessage);
      }

    } catch (error) {
      console.error('Failed to get AI response:', error);
      
      const errorMessage: ChatMessage = {
        id: `msg_${Date.now()}_error`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        type: 'text'
      };

      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        variant: 'destructive',
        title: 'Chat Error',
        description: 'Failed to get AI response. Please try again.'
      });
    } finally {
      setIsTyping(false);
    }
  }, [triggerHooks, user?.user_id, onMessageSent, onMessageReceived, toast]);

  // Generate AI response (mock implementation)
  const generateAIResponse = async (userInput: string, type: ChatMessage['type']): Promise<string> => {
    // In a real implementation, this would call the CopilotKit API
    const responses = {
      code: [
        "Here's a code solution for your request:\n\n```javascript\nfunction example() {\n  // Your code here\n  return 'Hello, World!';\n}\n```\n\nThis function demonstrates the concept you asked about.",
        "I can help you with that code. Here's an optimized version:\n\n```python\ndef optimized_function(data):\n    # Efficient implementation\n    return processed_data\n```\n\nThis approach is more efficient because it reduces complexity.",
        "Let me break down this code for you:\n\n```typescript\ninterface User {\n  id: string;\n  name: string;\n  email: string;\n}\n```\n\nThis TypeScript interface defines a user structure with proper typing."
      ],
      text: [
        "I understand your question. Based on the context, here's what I recommend: " + userInput.split(' ').slice(-3).join(' ') + " is a great approach for this use case.",
        "That's an interesting point about " + userInput.split(' ')[0] + ". Let me provide some insights and suggestions that might help you.",
        "I can help you with that. Here are some key considerations and best practices for your scenario."
      ]
    };

    const responseArray = responses[type as keyof typeof responses] || responses.text;
    return responseArray[Math.floor(Math.random() * responseArray.length)];
  };

  // Handle input submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading && !isTyping) {
      const messageType = inputValue.includes('```') || inputValue.includes('function') || inputValue.includes('class') ? 'code' : 'text';
      sendMessage(inputValue, messageType);
    }
  };


  return (
    <Card className={`flex flex-col ${className}`} style={{ height }}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          AI Assistant
          {config.features.chatAssistance && (
            <Badge variant="secondary" className="text-xs">
              Enhanced with CopilotKit
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-4 pb-4">
            {messages.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">Welcome to AI Assistant</p>
                <p className="text-sm">
                  I can help you with code, answer questions, and provide suggestions.
                  {enableCodeAssistance && " Try asking me about code or programming concepts!"}
                </p>
              </div>
              ) : (
                messages.map((message) => (
                  <ChatBubble
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    meta={{ confidence: message.metadata?.confidence }}
                  />
                ))
              )}
            
            {isTyping && (
              <div className="flex gap-3 mb-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="inline-block p-3 rounded-lg bg-muted border">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask me anything about code, get suggestions, or request help..."
              disabled={isLoading || isTyping}
              className="flex-1"
            />
            <Button 
              type="submit" 
              disabled={!inputValue.trim() || isLoading || isTyping}
              size="sm"
            >
              {isLoading || isTyping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
          
          {/* Quick Actions */}
          <div className="flex items-center gap-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => sendMessage("Help me debug this code", 'code')}
              disabled={isLoading || isTyping}
            >
              <Code className="h-3 w-3 mr-1" />
              Debug Code
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => sendMessage("Explain this concept", 'text')}
              disabled={isLoading || isTyping}
            >
              <Lightbulb className="h-3 w-3 mr-1" />
              Explain
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => sendMessage("Generate documentation", 'text')}
              disabled={isLoading || isTyping}
            >
              <FileText className="h-3 w-3 mr-1" />
              Document
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};