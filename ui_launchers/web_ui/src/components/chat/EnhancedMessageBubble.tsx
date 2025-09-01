"use client";

import React, { useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Bot, User, Copy, RefreshCw, Link as LinkIcon, Info } from 'lucide-react';
import { CopilotArtifacts, type CopilotArtifact } from './CopilotArtifacts';
import { MessageBubble as BasicMessageBubble } from './MessageBubble';

type Role = 'user' | 'assistant' | 'system';

export interface EnhancedMessageBubbleProps {
  role: Role;
  content: string;
  type?: string;
  language?: string;
  artifacts?: CopilotArtifact[];
  meta?: {
    confidence?: number;
    latencyMs?: number;
    model?: string;
    tokens?: number;
    cost?: number;
    persona?: string;
    mood?: string;
    intent?: string;
    reasoning?: string;
    sources?: string[];
  };
  onArtifactAction?: (artifactId: string, actionId: string) => void;
  onApprove?: (artifactId: string) => void;
  onReject?: (artifactId: string) => void;
  onApply?: (artifactId: string) => void;
  onCopy?: (content: string) => void;
  onRegenerate?: () => void;
  theme?: 'light' | 'dark';
}

// Renders additional meta/artifacts/actions when provided.
// Falls back to the simple MessageBubble when there are no extras.
const EnhancedMessageBubble: React.FC<EnhancedMessageBubbleProps> = (props) => {
  const {
    role,
    content,
    artifacts = [],
    meta,
    onArtifactAction,
    onApprove,
    onReject,
    onApply,
    onCopy,
    onRegenerate,
    theme = 'light',
  } = props;

  const hasExtras = !!(meta || (artifacts && artifacts.length) || onCopy || onRegenerate);

  // Simple path: reuse the basic bubble exactly
  const id = useMemo(() => Math.random().toString(36).slice(2), []);
  if (!hasExtras) {
    return <BasicMessageBubble message={{ id, role, content }} />;
  }

  const isUser = role === 'user';
  const isSystem = role === 'system';

  const handleCopy = () => {
    if (onCopy) onCopy(content);
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        navigator.clipboard.writeText(content);
      }
    } catch {}
  };

  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full">
          <Bot className="h-5 w-5 text-primary" />
        </Avatar>
      )}

      <Card className={`max-w-3xl shadow-md rounded-xl ${isUser ? 'bg-primary text-primary-foreground' : 'bg-card'}`}>
        <CardContent className="p-3 md:p-4 space-y-3">
          {/* Main content */}
          <p className={`whitespace-pre-wrap text-sm md:text-base ${isSystem ? 'text-foreground' : ''}`}>
            {content}
          </p>

          {/* Meta badges */}
          {meta && (
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {typeof meta.confidence === 'number' && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>
                  Confidence: {Math.round(meta.confidence * 100)}%
                </Badge>
              )}
              {typeof meta.latencyMs === 'number' && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>
                  Latency: {meta.latencyMs}ms
                </Badge>
              )}
              {meta.model && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>Model: {meta.model}</Badge>
              )}
              {typeof meta.tokens === 'number' && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>Tokens: {meta.tokens}</Badge>
              )}
              {typeof meta.cost === 'number' && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>
                  Cost: ${meta.cost.toFixed(4)}
                </Badge>
              )}
              {meta.intent && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>Intent: {meta.intent}</Badge>
              )}
              {meta.persona && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>Persona: {meta.persona}</Badge>
              )}
              {meta.mood && (
                <Badge variant={isUser ? 'secondary' : 'outline'}>Mood: {meta.mood}</Badge>
              )}
            </div>
          )}

          {/* Sources list */}
          {meta?.sources && meta.sources.length > 0 && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-medium opacity-80">
                <LinkIcon className="h-3.5 w-3.5" /> Sources
              </div>
              <ul className="list-disc pl-5 text-xs opacity-90 space-y-0.5">
                {meta.sources.map((src, i) => (
                  <li key={i} className="break-all">
                    {src}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Reasoning block */}
          {meta?.reasoning && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-medium opacity-80">
                <Info className="h-3.5 w-3.5" /> Reasoning
              </div>
              <div className="text-xs whitespace-pre-wrap opacity-90">
                {meta.reasoning}
              </div>
            </div>
          )}

          {/* Artifacts grid/list */}
          {artifacts && artifacts.length > 0 && (
            <div className="pt-1">
              <CopilotArtifacts
                artifacts={artifacts}
                onArtifactAction={onArtifactAction}
                onApprove={onApprove}
                onReject={onReject}
                onApply={onApply}
                theme={theme}
                showLineNumbers={true}
                enableCollapse={true}
                maxHeight="480px"
              />
            </div>
          )}

          {/* Message-level actions */}
          {(onCopy || onRegenerate) && (
            <div className="flex gap-2 justify-end pt-1">
              {onCopy && (
                <Button size="sm" variant={isUser ? 'secondary' : 'outline'} onClick={handleCopy}>
                  <Copy className="h-4 w-4 mr-2" /> Copy
                </Button>
              )}
              {onRegenerate && (
                <Button size="sm" variant={isUser ? 'secondary' : 'outline'} onClick={onRegenerate}>
                  <RefreshCw className="h-4 w-4 mr-2" /> Regenerate
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full">
          <User className="h-5 w-5 text-secondary" />
        </Avatar>
      )}
    </div>
  );
};

export default EnhancedMessageBubble;
