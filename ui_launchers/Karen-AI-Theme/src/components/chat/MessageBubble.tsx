"use client";

import React, { useState, useCallback } from 'react';
import type { ChatMessage } from '@/lib/types';
import { Avatar } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  User, Bot, Speaker, Copy, Check, Info, 
  ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, AlertTriangle, Zap, Clock 
} from 'lucide-react';
import { format } from 'date-fns';
import Image from 'next/image';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystemMessage = message.role === 'system';
  const [copied, setCopied] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const handleCopy = useCallback(() => {
    if (!message.content) return;
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [message.content]);

  const handleFeedback = (type: 'up' | 'down') => {
    setFeedback(feedback === type ? null : type);
    // Future: API call to record feedback
  };

  const isDegraded = message.metadata?.degraded_mode === true;
  const llm = message.metadata?.llm;
  const hasLlmInfo = llm && (llm.provider || llm.model_id);

  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
      {!isUser && (
        <Avatar className={`h-10 w-10 self-start shrink-0 flex items-center justify-center rounded-full shadow-sm ${isDegraded ? 'bg-amber-500/20' : 'bg-muted'}`}>
          <Bot className={`h-5 w-5 ${isDegraded ? 'text-amber-600' : 'text-primary'}`} />
        </Avatar>
      )}
      <Card className={`shadow-md rounded-2xl border-none transition-all duration-300 ${
        isUser
          ? 'max-w-xl bg-primary text-primary-foreground rounded-tr-none'
          : 'flex-1 w-full bg-card rounded-tl-none ring-1 ring-border/5'
      }`}>
        <CardContent className="p-3 md:p-4">
          <div className="flex justify-between items-start gap-2">
            <div className="flex-1 space-y-2 overflow-hidden">
              {message.content && (
                 <div className={`prose prose-sm md:prose-base dark:prose-invert max-w-none ${isSystemMessage ? 'text-foreground font-medium' : ''}`}>
                   <ReactMarkdown 
                     remarkPlugins={[remarkGfm]}
                     components={{
                       p: ({node, ...props}) => <p className="mb-2 last:mb-0 whitespace-pre-wrap leading-relaxed" {...props} />,
                       a: ({node, ...props}) => <a className="text-blue-400 hover:underline font-medium" target="_blank" rel="noreferrer" {...props} />,
                       ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                       ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-3 space-y-1" {...props} />,
                       li: ({node, ...props}) => <li className="mb-1" {...props} />,
                       code: ({node, className, children, ...props}: any) => {
                         const match = /language-(\w+)/.exec(className || '');
                         const isInline = !match && !String(children).includes('\n');
                         return !isInline ? (
                           <div className="relative group my-3">
                             <pre className="p-3 md:p-4 bg-[#1e1e1e] text-[#d4d4d4] rounded-xl overflow-x-auto font-mono text-xs md:text-sm border border-white/5">
                               <code className={className} {...props}>
                                 {children}
                               </code>
                             </pre>
                           </div>
                         ) : (
                           <code className="bg-muted px-1.5 py-0.5 rounded text-[0.9em] font-mono text-primary-foreground/90 bg-primary-foreground/10" {...props}>
                             {children}
                           </code>
                         )
                       }
                     }}
                   >
                     {message.content}
                   </ReactMarkdown>
                 </div>
              )}

              {/* Compact Metadata Badge — always visible for assistant messages */}
              {!isUser && message.role === 'assistant' && (hasLlmInfo || message.metadata?.degraded_mode) && (
                <div className="flex items-center gap-2 flex-wrap mt-2 overflow-hidden">
                  <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold tracking-wide uppercase border transition-all duration-300 ${
                    isDegraded
                      ? 'bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-sm shadow-amber-500/5'
                      : 'bg-primary/5 text-primary/80 border-primary/10 shadow-sm shadow-primary/5'
                  }`}>
                    {isDegraded ? (
                      <AlertTriangle className="h-3 w-3 animate-pulse" />
                    ) : (
                      <Zap className="h-3 w-3" />
                    )}
                    <span>{llm?.provider || 'system'}</span>
                    <span className="text-muted-foreground/50">·</span>
                    <span className="normal-case font-medium">
                      {llm?.model_name || (llm?.model_id ? 
                        llm.model_id.split(':').pop()?.split('/').pop()?.replace(/\.(gguf|bin)$/i, '').replace(/[-_]/g, ' ') 
                        : (message.metadata?.degraded_mode ? 'Degraded-Mode' : 'auto')
                      )}
                    </span>
                    {typeof llm?.duration === 'number' && (
                      <>
                        <span className="text-muted-foreground/50">·</span>
                        <Clock className="h-2.5 w-2.5" />
                        <span className="normal-case font-medium">{llm.duration.toFixed(1)}s</span>
                      </>
                    )}
                    {llm?.tokens_per_second && (
                      <>
                        <span className="text-muted-foreground/50">·</span>
                        <span className="normal-case font-medium text-emerald-500">{llm.tokens_per_second} tok/s</span>
                      </>
                    )}
                  </div>
                  {isDegraded && (
                    <span className="text-[10px] text-amber-500/70 font-medium tracking-tight animate-pulse">degraded mode</span>
                  )}
                </div>
              )}

              {/* Collapsible Metadata Details */}
              {!isUser && message.role === 'assistant' && hasLlmInfo && (
                <div className="mt-1 overflow-hidden transition-all duration-300">
                  <button 
                    onClick={() => setShowDetails(!showDetails)}
                    className="text-[10px] text-muted-foreground hover:text-primary flex items-center gap-1 transition-all group"
                  >
                    <Info className="h-3 w-3 group-hover:scale-110 transition-transform" />
                    <span>{showDetails ? 'Hide response details' : 'Show response details'}</span>
                    {showDetails ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  </button>
                  
                  {showDetails && (
                    <div className="mt-2 p-2.5 bg-muted/40 rounded-xl border border-border/30 text-[10px] grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono shadow-inner animate-in fade-in zoom-in-95 duration-200">
                      <div className="flex justify-between border-b border-border/20 pb-1 col-span-2 mb-1">
                          <span className="text-muted-foreground uppercase text-[8px] font-bold tracking-wider">Engine Metadata</span>
                          <span className="text-[8px] text-blue-500 font-bold uppercase">{llm.provider}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Provider:</span>
                        <span className="font-semibold">{llm.provider}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Model:</span>
                        <span className="font-semibold truncate max-w-[120px]" title={llm.model_id}>
                          {llm.model_id?.split(':').pop() || 'auto'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Source:</span>
                        <span className="font-semibold">{llm.source || 'direct'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Speed:</span>
                        <span className="font-semibold text-emerald-500">{llm.tokens_per_second || 'N/A'} tok/s</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Latency:</span>
                        <span className="font-semibold text-blue-500">{typeof llm.duration === 'number' ? llm.duration.toFixed(2) : 'N/A'}s</span>
                      </div>
                      {llm.is_degraded && (
                        <div className="flex justify-between col-span-2 pt-1 mt-1 border-t border-border/20">
                          <span className="text-muted-foreground">Status:</span>
                          <span className="font-semibold text-amber-500 flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3" /> Degraded Mode
                          </span>
                        </div>
                      )}
                      {llm.failure_reason && (
                        <div className="col-span-2 pt-1 mt-1 border-t border-border/20">
                          <span className="text-muted-foreground">Reason:</span>
                          <span className="font-semibold text-rose-400 ml-2 break-all">{llm.failure_reason}</span>
                        </div>
                      )}
                      {llm.usage && (
                        <div className="col-span-2 pt-1 mt-1 border-t border-border/20 flex justify-between">
                          <span className="text-muted-foreground">Tokens:</span>
                          <span className="font-semibold text-amber-500">
                            {llm.usage.prompt_tokens || 0}i + {llm.usage.completion_tokens || 0}o
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {message.structuredContent && Object.keys(message.structuredContent).length > 0 && (
                <div className="mt-3 flex flex-col gap-2">
                  {Object.entries(message.structuredContent).map(([key, value]) => (
                    <div key={key} className="bg-muted/30 border border-border/50 rounded-xl p-3 text-sm shadow-inner group">
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
          
          <div className={`flex items-center gap-3 mt-3 pt-2 border-t border-border/10 ${isUser ? 'justify-end' : 'justify-between'}`}>
            {!isUser && message.role === 'assistant' && (
              <div className="flex items-center gap-0.5 sm:gap-1 scale-90 sm:scale-100 origin-left">
                 <button 
                  onClick={() => handleFeedback('up')}
                  className={`p-1 rounded-md transition-all hover:bg-muted ${feedback === 'up' ? 'text-emerald-500 bg-emerald-500/10' : 'text-muted-foreground'}`}
                  title="Thumbs Up"
                 >
                   <ThumbsUp className={`h-3.5 w-3.5 ${feedback === 'up' ? 'fill-current' : ''}`} />
                 </button>
                 <button 
                  onClick={() => handleFeedback('down')}
                  className={`p-1 rounded-md transition-all hover:bg-muted ${feedback === 'down' ? 'text-rose-500 bg-rose-500/10' : 'text-muted-foreground'}`}
                  title="Thumbs Down"
                 >
                   <ThumbsDown className={`h-3.5 w-3.5 ${feedback === 'down' ? 'fill-current' : ''}`} />
                 </button>
                 <button 
                   onClick={handleCopy}
                   className={`p-1 rounded-md transition-all hover:bg-muted ml-1 flex items-center gap-1 ${copied ? 'text-emerald-500 bg-emerald-500/10' : 'text-muted-foreground'}`}
                   title="Copy to clipboard"
                 >
                   {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                   {copied && <span className="text-[10px] font-bold">Copied!</span>}
                 </button>
              </div>
            )}
            {isUser && (
              <button 
              onClick={handleCopy}
              className={`p-1 rounded-md transition-all hover:bg-primary-foreground/10 mr-1 flex items-center gap-1 scale-90 origin-right ${copied ? 'text-white bg-white/10' : 'text-primary-foreground/60'}`}
              title="Copy your message"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
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
