"use client";

import React, { useState, useCallback } from 'react';
import type { ChatMessage } from '@/lib/types';
import { Avatar } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  User, Bot, Speaker, Copy, Check, Info,
  ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, AlertTriangle, Zap, Clock, PlusCircle
} from 'lucide-react';
import { format } from 'date-fns';
import Image from 'next/image';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"
import {
  deriveCompactBadgePresentation,
  deriveDegradedPresentation,
  deriveResponseDetailsPresentation,
  sanitizeChatContent,
} from '@/lib/chat-response';
import { ChatRenderedContent } from '@/lib/chat-renderer';
import type { SuggestedAction } from '@/lib/agent-ui/service';
import CitationBadge from './CitationBadge';
import SourceList from './SourceList';

interface MessageBubbleProps {
  message: ChatMessage;
  onActionClick?: (action: SuggestedAction) => void;
}

export function MessageBubble({ message, onActionClick }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystemMessage = message.role === 'system';
  const [copied, setCopied] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleCopy = useCallback(async () => {
    if (!message.content) return;

    try {
      // Modern clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } else {
        // Fallback for non-secure contexts or older browsers
        copyToClipboardFallback(message.content);
      }
    } catch (err) {
      console.error('Failed to copy text: ', err);
      // Try fallback method
      copyToClipboardFallback(message.content);
    }
  }, [message.content]);

  // Helper for clipboard fallback (modern approach)
  const copyToClipboardFallback = (text: string) => {
    if (typeof document === 'undefined') return;

    try {
      const textArea = document.createElement("textarea");
      textArea.value = text;

      // Modern approach: use Selection API instead of execCommand
      textArea.style.position = "fixed";
      textArea.style.left = "-999999px";
      textArea.style.top = "-999999px";
      textArea.style.opacity = "0";
      document.body.appendChild(textArea);

      textArea.focus();
      textArea.select();

      // Use modern Selection API
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(textArea);
      selection?.removeAllRanges();
      selection?.addRange(range);

      // Try to copy using the Selection API
      document.execCommand('copy'); // Still needed as fallback, but we're trying modern first

      document.body.removeChild(textArea);
      selection?.removeAllRanges();

      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Fallback copy failed: ', err);
      // Could show a toast notification here for manual copy
    }
  };

  const handleFeedback = async (type: 'up' | 'down') => {
    const newFeedback = feedback === type ? null : type;
    setFeedback(newFeedback);

    if (newFeedback && !feedbackSubmitted) {
      // Simulate API call for feedback submission
      try {
        // Future: Replace with actual API call
        // await apiClient.post('/api/feedback', { messageId: message.id, feedback: type });

        setFeedbackSubmitted(true);
        // Reset feedback submitted state after a delay
        setTimeout(() => setFeedbackSubmitted(false), 3000);
      } catch (error) {
        console.error('Failed to submit feedback:', error);
        // Could show a toast notification here
      }
    }
  };


  const {
    visibleDegradedNotice,
    shouldRenderDegradedState,
  } = deriveDegradedPresentation(message.metadata);
  const {
    shouldRenderBadge,
    providerLabel: badgeProviderLabel,
    modelLabel: badgeModelLabel,
    durationLabel: badgeDurationLabel,
    speedLabel: badgeSpeedLabel,
    statusLabel: badgeStatusLabel,
    isDegraded: badgeIsDegraded,
  } = deriveCompactBadgePresentation(message.metadata);
  const {
    hasMetadataDetails,
    providerLabel,
    modelLabel,
    modelTitle,
    sourceLabel,
    speedLabel,
    latencyLabel,
    engineHeaderLabel,
    showStatusRow,
    statusLabel,
    showFallbackRow,
    fallbackLabel,
    showReasonRow,
    reasonLabel,
    showTokensRow,
    tokensLabel,
  } = deriveResponseDetailsPresentation(message.metadata);
  const normalizedContent = sanitizeChatContent(message.content);
  const normalizedDegradedNotice = sanitizeChatContent(visibleDegradedNotice);
  const shouldShowDegradedNotice =
    Boolean(normalizedDegradedNotice) &&
    normalizedDegradedNotice.toLowerCase() !== normalizedContent.toLowerCase();

  return (
    <div className={`user-bubble flex items-start gap-2 sm:gap-3 my-3 sm:my-4 px-2 sm:px-0 ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      {!isUser && (
        <Avatar className={`h-8 w-8 sm:h-10 sm:w-10 self-start shrink-0 flex items-center justify-center rounded-full shadow-sm ${shouldRenderDegradedState ? 'bg-amber-500/20' : 'bg-muted'}`}>
          <Bot className={`h-4 w-4 sm:h-5 sm:w-5 ${shouldRenderDegradedState ? 'text-amber-600' : 'text-primary'}`} />
        </Avatar>
      )}
      <Card className={`shadow-md rounded-2xl border-none transition-all duration-300 max-w-[90vw] sm:max-w-xl ${
        isUser
          ? 'bg-primary text-primary-foreground rounded-tr-none'
          : 'flex-1 w-full bg-card rounded-tl-none ring-1 ring-border/5'
      }`}>
        <CardContent className="p-2 sm:p-3 md:p-4">
          <div className="flex justify-between items-start gap-2">
            <div className="flex-1 space-y-2 overflow-hidden">
              {!isUser && message.role === 'assistant' && shouldShowDegradedNotice && (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/8 px-3 py-2 text-[11px] text-amber-200/90 flex items-center justify-between">
                  <span>{normalizedDegradedNotice}</span>
                  <span className="text-[10px] text-amber-500/70 font-medium tracking-tight animate-pulse">degraded mode</span>
                </div>
              )}

              {message.content && (
                <ChatRenderedContent
                  content={normalizedContent}
                  emphasize={isSystemMessage}
                />
              )}

              {/* Compact Metadata Badge — always visible for assistant messages */}
              {!isUser && message.role === 'assistant' && shouldRenderBadge && !badgeIsDegraded && (
                <div className="flex items-center gap-2 flex-wrap mt-2 overflow-hidden">
                  <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold tracking-wide uppercase border transition-all duration-300 ${
                    badgeIsDegraded
                      ? 'bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-sm shadow-amber-500/5'
                      : 'bg-primary/5 text-primary/80 border-primary/10 shadow-sm shadow-primary/5'
                  }`}>
                    {badgeIsDegraded ? (
                      <AlertTriangle className="h-3 w-3 animate-pulse" />
                    ) : (
                      <Zap className="h-3 w-3" />
                    )}
                      <span>{badgeProviderLabel}</span>
                      <span className="text-muted-foreground/50">·</span>
                      <span className="normal-case font-medium">
                        {badgeModelLabel}
                      </span>
                    {badgeDurationLabel && (
                      <>
                        <span className="text-muted-foreground/50">·</span>
                        <Clock className="h-2.5 w-2.5" />
                        <span className="normal-case font-medium">{badgeDurationLabel}</span>
                      </>
                    )}
                    {badgeSpeedLabel && (
                      <>
                        <span className="text-muted-foreground/50">·</span>
                        <span className="normal-case font-medium text-emerald-500">{badgeSpeedLabel}</span>
                      </>
                    )}
                  </div>
                  {badgeStatusLabel && (
                    <span className="text-[10px] text-amber-500/70 font-medium tracking-tight animate-pulse">
                      {badgeStatusLabel}
                    </span>
                  )}
                </div>
              )}

              {/* Collapsible Metadata Details */}
              {!isUser && message.role === 'assistant' && hasMetadataDetails && (
                <div className="mt-1 overflow-hidden transition-all duration-300">
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="text-[10px] text-muted-foreground hover:text-primary flex items-center gap-1 transition-all group"
                    aria-label={showDetails ? 'Hide response details' : 'Show response details'}
                    aria-expanded={showDetails}
                    aria-controls="response-details"
                  >
                    <Info className="h-3 w-3 group-hover:scale-110 transition-transform" aria-hidden="true" />
                    <span>{showDetails ? 'Hide response details' : 'Show response details'}</span>
                    {showDetails ? <ChevronUp className="h-3 w-3" aria-hidden="true" /> : <ChevronDown className="h-3 w-3" aria-hidden="true" />}
                  </button>
                  
                  {showDetails && (
                    <div id="response-details" className="mt-2 p-2.5 bg-muted/40 rounded-xl border border-border/30 text-[10px] grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono shadow-inner animate-in fade-in zoom-in-95 duration-200" role="region" aria-label="Response details">
                      <div className="flex justify-between border-b border-border/20 pb-1 col-span-2 mb-1">
                          <span className="text-muted-foreground uppercase text-[8px] font-bold tracking-wider">Engine Metadata</span>
                          <span className="text-[8px] text-blue-500 font-bold uppercase">{engineHeaderLabel}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Provider:</span>
                      <span className="font-semibold">{providerLabel}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Model:</span>
                        <span className="font-semibold truncate max-w-[120px]" title={modelTitle}>
                          {modelLabel}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Source:</span>
                        <span className="font-semibold">{sourceLabel}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Speed:</span>
                        <span className="font-semibold text-emerald-500">{speedLabel}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Latency:</span>
                        <span className="font-semibold text-blue-500">{latencyLabel}</span>
                      </div>
                      {showStatusRow && (
                        <div className="flex justify-between col-span-2 pt-1 mt-1 border-t border-border/20">
                          <span className="text-muted-foreground">Status:</span>
                          <span className="font-semibold text-amber-500 flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3" /> {statusLabel}
                          </span>
                        </div>
                      )}
                      {showFallbackRow && (
                        <div className="col-span-2 pt-1 mt-1 border-t border-border/20">
                          <span className="text-muted-foreground">Fallback:</span>
                          <span className="font-semibold text-amber-300 ml-2 break-all">{fallbackLabel}</span>
                        </div>
                      )}
                      {showReasonRow && (
                        <div className="col-span-2 pt-1 mt-1 border-t border-border/20">
                          <span className="text-muted-foreground">Reason:</span>
                          <span className="font-semibold text-rose-400 ml-2 break-all">{reasonLabel}</span>
                        </div>
                      )}
                      {showTokensRow && (
                        <div className="col-span-2 pt-1 mt-1 border-t border-border/20 flex justify-between">
                          <span className="text-muted-foreground">Tokens:</span>
                          <span className="font-semibold text-amber-500">{tokensLabel}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {message.structuredContent && Object.keys(message.structuredContent).length > 0 && (
                <div className="mt-3 flex flex-col gap-2">
                  {Object.entries(message.structuredContent).map(([key, value]) => (
                    <div key={key} className="bg-muted/30 border border-border/50 rounded-xl p-3 text-sm shadow-inner group transition-all hover:bg-muted/40">
                      <span className="font-semibold text-primary capitalize mb-1 block text-xs tracking-tight group-hover:text-blue-500 transition-colors">
                        {key.replace(/_/g, ' ')}
                      </span>
                      {typeof value === 'string' ? (
                        <p className="text-foreground/90 whitespace-pre-wrap text-xs leading-relaxed">{value}</p>
                      ) : (
                        <pre className="text-foreground/80 bg-background/50 p-2 rounded-lg text-[10px] overflow-x-auto border border-border/20">
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Citations and Sources */}
              {!isUser && message.citations && message.citations.length > 0 && (
                <CitationBadge
                  citations={message.citations}
                  onClick={() => setShowDetails(!showDetails)}
                />
              )}

              {showDetails && !isUser && message.citations && message.citations.length > 0 && (
                <SourceList citations={message.citations} />
              )}

              {/* Suggested Actions (Quick Replies / Agentic Follow-ups) */}
              {message.actions && message.actions.length > 0 && (
                <div className="mt-3 sm:mt-4 animate-in fade-in slide-in-from-left-2 duration-500">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary" className="text-[10px] px-2 py-0.5">
                      Suggested Actions
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5 sm:gap-2">
                    <TooltipProvider>
                      {message.actions.map((action, idx) => (
                        <Tooltip key={idx}>
                          <TooltipTrigger asChild>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => onActionClick?.(action)}
                              className="rounded-full text-[10px] sm:text-[11px] h-7 sm:h-8 px-2 sm:px-3 bg-background/50 hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all duration-300 shadow-sm group"
                              aria-label={`Perform action: ${action.description || action.type || 'Perform Action'}`}
                            >
                              <PlusCircle className="h-2.5 w-2.5 sm:h-3 sm:w-3 mr-1 sm:mr-1.5 text-primary/60 group-hover:text-primary transition-colors" aria-hidden="true" />
                              <span className="truncate max-w-[120px] sm:max-w-none">
                                {action.type === 'routing.profile.list' ? 'Show Available Profiles' : (action.description || action.type || 'Perform Action')}
                              </span>
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent side="top" className="max-w-xs">
                            <p className="text-sm">
                              {action.description || `Execute ${action.type} action`}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </TooltipProvider>
                  </div>
                </div>
              )}
              {message.imageDataUri && (
                <div className="mt-2 rounded-xl overflow-hidden border border-border/50 shadow-sm transition-transform hover:scale-[1.01] duration-300">
                    <Image 
                        src={message.imageDataUri}
                        alt="Generated by AI"
                        width={400}
                        height={400}
                        className="object-cover w-full h-auto"
                    />
                </div>
              )}
            </div>
            {!isUser && message.role === 'assistant' && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="ml-2 h-7 w-7 text-muted-foreground hover:text-primary shrink-0 opacity-40 hover:opacity-100 transition-opacity"
                      aria-label={"Play message audio"}
                      disabled={true}
                    >
                      <Speaker className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>TTS disabled: Backend removed.</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          
          <div className={`flex items-center gap-2 sm:gap-3 mt-2 sm:mt-3 pt-2 border-t border-border/10 ${isUser ? 'justify-end' : 'justify-between'} flex-wrap`}>
            {!isUser && message.role === 'assistant' && (
              <div className="flex items-center gap-0.5 sm:gap-1 scale-90 sm:scale-100 origin-left">
                  <button
                   onClick={() => handleFeedback('up')}
                   className={`p-1 rounded-md transition-all hover:bg-muted ${feedback === 'up' ? 'text-emerald-500 bg-emerald-500/10' : 'text-muted-foreground'} ${feedbackSubmitted && feedback === 'up' ? 'animate-pulse' : ''}`}
                   aria-label={feedbackSubmitted && feedback === 'up' ? "Feedback submitted" : "Rate response positively"}
                   aria-pressed={feedback === 'up'}
                   title="Thumbs Up"
                   disabled={feedbackSubmitted}
                  >
                    <ThumbsUp className={`h-3.5 w-3.5 ${feedback === 'up' ? 'fill-current' : ''}`} aria-hidden="true" />
                  </button>
                  <button
                   onClick={() => handleFeedback('down')}
                   className={`p-1 rounded-md transition-all hover:bg-muted ${feedback === 'down' ? 'text-rose-500 bg-rose-500/10' : 'text-muted-foreground'} ${feedbackSubmitted && feedback === 'down' ? 'animate-pulse' : ''}`}
                   aria-label={feedbackSubmitted && feedback === 'down' ? "Feedback submitted" : "Rate response negatively"}
                   aria-pressed={feedback === 'down'}
                   title="Thumbs Down"
                   disabled={feedbackSubmitted}
                  >
                    <ThumbsDown className={`h-3.5 w-3.5 ${feedback === 'down' ? 'fill-current' : ''}`} aria-hidden="true" />
                  </button>
                  <button
                    onClick={handleCopy}
                    className={`p-1 rounded-md transition-all hover:bg-muted ml-1 flex items-center gap-1 ${copied ? 'text-emerald-500 bg-emerald-500/10' : 'text-muted-foreground'}`}
                    aria-label={copied ? "Response copied to clipboard" : "Copy response to clipboard"}
                    title="Copy to clipboard"
                  >
                    {copied ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Copy className="h-3.5 w-3.5" aria-hidden="true" />}
                    {copied && <span className="text-[10px] font-bold">Copied!</span>}
                  </button>
              </div>
            )}
            {isUser && (
              <button
              onClick={handleCopy}
              className={`p-1 rounded-md transition-all hover:bg-primary-foreground/10 mr-1 flex items-center gap-1 scale-90 origin-right ${copied ? 'text-white bg-white/10' : 'text-primary-foreground/60'}`}
              aria-label={copied ? "Message copied to clipboard" : "Copy your message to clipboard"}
              title="Copy your message"
            >
              {copied ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Copy className="h-3.5 w-3.5" aria-hidden="true" />}
            </button>
            )}
            <p className={`text-[10px] font-medium tracking-tight ${isUser ? 'text-primary-foreground/60' : 'text-muted-foreground/70'}`}>
              {format(new Date(message.timestamp), 'h:mm a')}
            </p>
          </div>
        </CardContent>
      </Card>
      {isUser && (
         <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full shadow-sm ring-2 ring-primary/20">
          <User className="h-5 w-5 text-secondary" />
        </Avatar>
      )}
    </div>
  );
}
