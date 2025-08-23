'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Bot, User, Code, FileText, Copy, Check, X, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MetaBar } from './MetaBar';
import { CopilotArtifacts, type CopilotArtifact } from './CopilotArtifacts';
import { webUIConfig } from '@/lib/config';
import { useToast } from '@/hooks/use-toast';

// Syntax highlighting
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

export interface EnhancedMessageBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: 'text' | 'code' | 'suggestion' | 'analysis' | 'documentation';
  language?: string;
  artifacts?: CopilotArtifact[];
  meta?: {
    confidence?: number;
    annotations?: number;
    latencyMs?: number;
    model?: string;
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

// Utility function to extract and parse code blocks
const extractCodeBlocks = (content: string) => {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const blocks: Array<{
    language: string;
    code: string;
    startIndex: number;
    endIndex: number;
  }> = [];
  
  let match;
  while ((match = codeBlockRegex.exec(content)) !== null) {
    blocks.push({
      language: match[1] || 'text',
      code: match[2].trim(),
      startIndex: match.index,
      endIndex: match.index + match[0].length
    });
  }
  
  return blocks;
};

// Component for rendering code blocks with syntax highlighting
const CodeBlock: React.FC<{
  code: string;
  language: string;
  theme?: 'light' | 'dark';
  onCopy?: (code: string) => void;
}> = ({ code, language, theme = 'light', onCopy }) => {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);
  
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      if (onCopy) onCopy(code);
      toast({
        title: 'Copied',
        description: 'Code copied to clipboard'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy code to clipboard'
      });
    }
  }, [code, onCopy, toast]);
  
  return (
    <div className="relative group">
      <div className="flex items-center justify-between bg-gray-100 dark:bg-gray-800 px-3 py-2 rounded-t-md">
        <Badge variant="secondary" className="text-xs">
          <Code className="h-3 w-3 mr-1" />
          {language}
        </Badge>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {copied ? (
            <Check className="h-3 w-3 text-green-500" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
        </Button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={theme === 'dark' ? oneDark : oneLight}
        customStyle={{
          margin: 0,
          borderTopLeftRadius: 0,
          borderTopRightRadius: 0,
          borderBottomLeftRadius: '0.375rem',
          borderBottomRightRadius: '0.375rem',
          fontSize: '0.875rem'
        }}
        showLineNumbers={code.split('\n').length > 5}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};

// Component for rendering enhanced content with code blocks
const EnhancedContent: React.FC<{
  content: string;
  type?: string;
  language?: string;
  theme?: 'light' | 'dark';
  onCopy?: (content: string) => void;
}> = ({ content, type, language, theme = 'light', onCopy }) => {
  const codeBlocks = useMemo(() => extractCodeBlocks(content), [content]);
  
  // If no code blocks, render as plain text
  if (codeBlocks.length === 0) {
    return (
      <div className="whitespace-pre-wrap break-words leading-relaxed">
        <span className="text-sm md:text-base font-normal tracking-normal">
          {content}
        </span>
      </div>
    );
  }
  
  // Render content with embedded code blocks
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  
  codeBlocks.forEach((block, index) => {
    // Add text before code block
    if (block.startIndex > lastIndex) {
      const textContent = content.slice(lastIndex, block.startIndex);
      if (textContent.trim()) {
        parts.push(
          <div key={`text-${index}`} className="whitespace-pre-wrap break-words leading-relaxed mb-3">
            <span className="text-sm md:text-base font-normal tracking-normal">
              {textContent}
            </span>
          </div>
        );
      }
    }
    
    // Add code block
    parts.push(
      <div key={`code-${index}`} className="my-3">
        <CodeBlock
          code={block.code}
          language={block.language}
          theme={theme}
          onCopy={onCopy}
        />
      </div>
    );
    
    lastIndex = block.endIndex;
  });
  
  // Add remaining text after last code block
  if (lastIndex < content.length) {
    const textContent = content.slice(lastIndex);
    if (textContent.trim()) {
      parts.push(
        <div key="text-final" className="whitespace-pre-wrap break-words leading-relaxed mt-3">
          <span className="text-sm md:text-base font-normal tracking-normal">
            {textContent}
          </span>
        </div>
      );
    }
  }
  
  return <div>{parts}</div>;
};

export const EnhancedMessageBubble: React.FC<EnhancedMessageBubbleProps> = ({
  role,
  content,
  type,
  language,
  artifacts = [],
  meta,
  onArtifactAction,
  onApprove,
  onReject,
  onApply,
  onCopy,
  onRegenerate,
  theme = 'light'
}) => {
  const { toast } = useToast();
  const [showArtifacts, setShowArtifacts] = useState(true);
  const [activeTab, setActiveTab] = useState<'content' | 'artifacts'>('content');
  
  const isUser = role === 'user';
  const isSystem = role === 'system';
  const hasArtifacts = artifacts.length > 0;
  
  const filteredMeta = meta ? {
    model: webUIConfig.showModelBadge ? meta.model : undefined,
    latencyMs: webUIConfig.showLatencyBadge ? meta.latencyMs : undefined,
    confidence: webUIConfig.showConfidenceBadge ? meta.confidence : undefined,
    annotations: meta.annotations,
    persona: meta.persona,
    mood: meta.mood,
    intent: meta.intent,
    reasoning: meta.reasoning,
    sources: meta.sources,
  } : undefined;
  
  const shouldShowMeta =
    role === 'assistant' &&
    filteredMeta &&
    Object.values(filteredMeta).some(v => v !== undefined);

  // Handle copy action
  const handleCopy = useCallback(async (textToCopy?: string) => {
    const copyContent = textToCopy || content;
    try {
      await navigator.clipboard.writeText(copyContent);
      if (onCopy) onCopy(copyContent);
      toast({
        title: 'Copied',
        description: 'Content copied to clipboard'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy content to clipboard'
      });
    }
  }, [content, onCopy, toast]);

  // Get type-specific styling
  const getTypeIcon = () => {
    switch (type) {
      case 'code':
        return <Code className="h-3 w-3" />;
      case 'documentation':
        return <FileText className="h-3 w-3" />;
      default:
        return null;
    }
  };

  const getTypeBadge = () => {
    if (!type || type === 'text') return null;
    
    return (
      <Badge variant="secondary" className="text-xs mb-2">
        {getTypeIcon()}
        <span className="ml-1 capitalize">{type}</span>
        {language && <span className="ml-1">({language})</span>}
      </Badge>
    );
  };

  return (
    <div className={`flex gap-3 mb-6 ${isUser ? 'flex-row-reverse' : 'flex-row'} group`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-9 h-9 md:w-10 md:h-10 rounded-full flex items-center justify-center shadow-sm transition-all duration-200 ${
          isUser 
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white hover:shadow-md' 
            : isSystem
            ? 'bg-gradient-to-br from-gray-400 to-gray-500 text-white'
            : 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white hover:shadow-md'
        }`}
      >
        {isUser ? (
          <User className="h-4 w-4 md:h-5 md:w-5" />
        ) : (
          <Bot className="h-4 w-4 md:h-5 md:w-5" />
        )}
      </div>

      {/* Message content */}
      <div className={`flex-1 max-w-[85%] md:max-w-[80%] lg:max-w-[75%] ${isUser ? 'text-right' : 'text-left'}`}>
        {/* Main message bubble */}
        <div
          className={`inline-block p-4 md:p-5 rounded-2xl shadow-sm transition-all duration-200 hover:shadow-md w-full ${
            isUser 
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white' 
              : isSystem
              ? 'bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-800 dark:to-gray-750 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
          }`}
        >
          {/* Type badge */}
          {!isUser && getTypeBadge()}
          
          {/* Content with artifacts tabs */}
          {hasArtifacts && !isUser ? (
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'content' | 'artifacts')}>
              <TabsList className="grid w-full grid-cols-2 mb-3">
                <TabsTrigger value="content">Response</TabsTrigger>
                <TabsTrigger value="artifacts">
                  Artifacts ({artifacts.length})
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="content" className="mt-0">
                <EnhancedContent
                  content={content}
                  type={type}
                  language={language}
                  theme={theme}
                  onCopy={handleCopy}
                />
              </TabsContent>
              
              <TabsContent value="artifacts" className="mt-0">
                <CopilotArtifacts
                  artifacts={artifacts}
                  onArtifactAction={onArtifactAction}
                  onApprove={onApprove}
                  onReject={onReject}
                  onApply={onApply}
                  theme={theme}
                  showLineNumbers={true}
                  enableCollapse={true}
                  className="max-h-96"
                />
              </TabsContent>
            </Tabs>
          ) : (
            <EnhancedContent
              content={content}
              type={type}
              language={language}
              theme={theme}
              onCopy={handleCopy}
            />
          )}
        </div>
        
        {/* Action buttons for assistant messages */}
        {!isUser && (
          <div className="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCopy()}
              className="h-6 px-2 text-xs"
            >
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
            
            {onRegenerate && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onRegenerate}
                className="h-6 px-2 text-xs"
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Regenerate
              </Button>
            )}
            
            {hasArtifacts && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowArtifacts(!showArtifacts)}
                className="h-6 px-2 text-xs"
              >
                {showArtifacts ? (
                  <ChevronUp className="h-3 w-3 mr-1" />
                ) : (
                  <ChevronDown className="h-3 w-3 mr-1" />
                )}
                {showArtifacts ? 'Hide' : 'Show'} Artifacts
              </Button>
            )}
          </div>
        )}
        
        {/* Meta information */}
        {shouldShowMeta && (
          <div className="mt-2">
            <MetaBar {...filteredMeta} />
          </div>
        )}
        
        {/* Timestamp */}
        <div className={`text-xs text-gray-500 dark:text-gray-400 mt-1 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

export default EnhancedMessageBubble;