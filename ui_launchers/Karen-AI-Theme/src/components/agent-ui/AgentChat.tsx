'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useAgentStore } from '@/lib/agent-ui/store';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Loader2 } from 'lucide-react';
import { Agent } from '@/lib/agent-ui/service';

interface AgentChatProps {
  agent: Agent;
  className?: string;
  onClose?: () => void;
}

export function AgentChat({ agent, className = '', onClose }: AgentChatProps) {
  const { messages, sendMessage, initSession, loading } = useAgentStore();
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const agentMessages = messages[agent.id] || [];
  const isAgentLoading = loading[agent.id] || false;

  useEffect(() => {
    initSession(agent.id);
  }, [agent.id, initSession]);

  useEffect(() => {
    // Auto scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [agentMessages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isAgentLoading) return;
    
    sendMessage(agent.id, inputValue.trim());
    setInputValue('');
  };

  return (
    <div className={`flex flex-col h-full bg-background ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h3 className="font-semibold">{agent.name} {isAgentLoading && <span className="ml-2 text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full animate-pulse">Thinking...</span>}</h3>
          <p className="text-xs text-muted-foreground">{agent.description}</p>
        </div>
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4 pb-4">
          {agentMessages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground pt-12">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                <span className="text-2xl">👋</span>
              </div>
              <p>Say hello to {agent.name} to get started.</p>
            </div>
          ) : (
            agentMessages.map((msg) => (
              <div key={msg.id} className={msg.isLoading ? "opacity-70 animate-pulse" : ""}>
                <MessageBubble 
                  message={{
                    id: msg.id,
                    role: msg.role,
                    content: msg.content,
                    timestamp: new Date(msg.timestamp),
                    structuredContent: msg.structured_content,
                    actions: msg.actions,
                    metadata: msg.metadata,
                  }} 
                />
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t bg-card">
        <form onSubmit={handleSubmit} className="flex gap-2 relative">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={`Message ${agent.name}...`}
            className="flex-1 bg-background"
            disabled={isAgentLoading}
            autoFocus
          />
          <Button type="submit" disabled={!inputValue.trim() || isAgentLoading}>
            {isAgentLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </form>
      </div>
    </div>
  );
}
