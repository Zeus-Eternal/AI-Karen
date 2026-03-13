import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  MessageSquare, 
  Bot, 
  Copy, 
  Check, 
  ThumbsUp, 
  ThumbsDown, 
  MoreVertical,
  Edit,
  RefreshCw,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useAdaptiveInterface } from './adaptive-interface-hooks';
import { useAdaptiveLayout } from './adaptive-layout-hooks';

interface SmartMessageBubbleProps {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  metadata?: {
    modality?: 'text' | 'code' | 'image' | 'audio';
    pluginId?: string;
    artifactId?: string;
    workflowId?: string;
    intent?: string;
    confidence?: number;
    memoryOps?: unknown;
    suggestions?: string[];
    actions?: Array<{
      id: string;
      title: string;
      description: string;
      riskLevel: 'safe' | 'privileged' | 'evil-mode-only';
    }>;
  };
  className?: string;
  onExecuteAction?: (actionId: string) => void;
  onEdit?: (id: string, newContent: string) => void;
  onRetry?: (id: string) => void;
  onFeedback?: (id: string, isPositive: boolean) => void;
  onCopy?: (content: string) => void;
  onToggleSpeech?: (id: string, enabled: boolean) => void;
}

/**
 * SmartMessageBubble component that provides enhanced message display
 * with interactive features and adaptive behavior based on user expertise level.
 * Implements the Copilot-first smart message system.
 */
export const SmartMessageBubble: React.FC<SmartMessageBubbleProps> = ({
  id,
  content,
  role,
  timestamp,
  metadata,
  className,
  onExecuteAction,
  onEdit,
  onRetry,
  onFeedback,
  onCopy,
  onToggleSpeech
}) => {
  const { adaptationPolicy, expertiseLevel } = useAdaptiveInterface();
  const { isMobile } = useAdaptiveLayout();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(content);
  const [isCopied, setIsCopied] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  
  const messageRef = useRef<HTMLDivElement>(null);
  const editInputRef = useRef<HTMLTextAreaElement>(null);

  // Focus edit input when editing starts
  useEffect(() => {
    if (isEditing && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.setSelectionRange(
        editInputRef.current.value.length,
        editInputRef.current.value.length
      );
    }
  }, [isEditing]);

  // Reset copy state after 2 seconds
  useEffect(() => {
    if (isCopied) {
      const timer = setTimeout(() => setIsCopied(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [isCopied]);

  // Handle copy action
  const handleCopy = () => {
    onCopy?.(content);
    navigator.clipboard.writeText(content);
    setIsCopied(true);
  };

  // Handle edit save
  const handleSaveEdit = () => {
    onEdit?.(id, editedContent);
    setIsEditing(false);
  };

  // Handle edit cancel
  const handleCancelEdit = () => {
    setEditedContent(content);
    setIsEditing(false);
  };

  // Handle feedback
  const handleFeedback = (isPositive: boolean) => {
    setFeedback(isPositive ? 'positive' : 'negative');
    onFeedback?.(id, isPositive);
  };

  // Handle speech toggle
  const handleToggleSpeech = () => {
    const newSpeakingState = !isSpeaking;
    setIsSpeaking(newSpeakingState);
    onToggleSpeech?.(id, newSpeakingState);
    
    // In a real implementation, this would use the Web Speech API
    if (newSpeakingState) {
      // Placeholder for speech synthesis
      console.log('Speaking message:', content);
    } else {
      // Placeholder for stopping speech
      console.log('Stopping speech');
    }
  };

  // Format timestamp
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Truncate content for preview
  const getPreviewContent = () => {
    if (content.length <= 150 || isExpanded) return content;
    return content.substring(0, 150) + '...';
  };

  // Determine if message should show advanced features
  const showAdvancedFeatures = adaptationPolicy.showAdvancedFeatures && 
                               expertiseLevel !== 'beginner';

  // Determine if message should show debug info
  const showDebugInfo = adaptationPolicy.showDebugInfo && expertiseLevel === 'expert';

  return (
    <div
      ref={messageRef}
      className={cn(
        'group relative flex flex-col rounded-[var(--component-card-border-radius,var(--radius-lg))] text-[var(--component-card-foreground)] transition-all duration-300 ease-in-out focus-within:ring-2 focus-within:ring-[var(--component-card-ring)] focus-within:ring-offset-2 focus-within:ring-offset-[var(--component-card-ring-offset,var(--color-neutral-50))] bg-[var(--component-card-background)] border-[var(--component-card-border)] shadow-[var(--component-card-shadow)] overflow-hidden',
        {
          'ml-auto max-w-[85%]': role === 'user',
          'mr-auto max-w-[85%]': role === 'assistant',
          'mx-auto max-w-[90%]': role === 'system',
          'border-destructive/50 bg-destructive/5': role === 'system',
          'mobile': isMobile,
          'guided-mode': adaptationPolicy.guidedMode
        },
        className
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="py-[var(--space-md)] border-b border-[var(--component-card-border)] pb-2 pt-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={cn(
              "rounded-full p-1",
              role === 'user' ? 'bg-primary text-primary-foreground' : 
              role === 'assistant' ? 'bg-secondary text-secondary-foreground' : 
              'bg-muted text-muted-foreground'
            )}>
              {role === 'user' ? (
                <MessageSquare className="h-4 w-4" />
              ) : role === 'assistant' ? (
                <Bot className="h-4 w-4" />
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-zap h-4 w-4">
                  <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"></path>
                </svg>
              )}
            </div>
            <div>
              <div className="font-medium text-sm">
                {role === 'user' ? 'You' : role === 'assistant' ? 'KAREN' : 'System'}
              </div>
              {adaptationPolicy.showTimestamps && (
                <div className="text-xs text-muted-foreground">
                  {formatTime(timestamp)}
                </div>
              )}
            </div>
            {metadata?.intent && (
              <Badge variant="outline" className="text-xs">
                {metadata.intent}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {showActions && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => setShowActions(!showActions)}
              >
                <MoreVertical className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>
      </div>
      
      <div className="py-[var(--space-md)] px-4 pb-3 pt-0">
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              ref={editInputRef}
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full min-h-[100px] p-2 text-sm bg-background text-foreground border rounded-md resize-none"
              style={{ 
                fontSize: `calc(var(--font-size, 1rem) * ${adaptationPolicy.simplifiedUI ? 1.1 : 1})` 
              }}
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancelEdit}
              >
                Cancel
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleSaveEdit}
              >
                Save
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Message content */}
            <div
              className="message-content whitespace-pre-wrap break-words"
              style={{
                fontSize: `calc(var(--font-size, 1rem) * ${adaptationPolicy.simplifiedUI ? 1.1 : 1})`
              }}
            >
              {adaptationPolicy.markdownSupport ? (
                // In a real implementation, this would use a markdown renderer
                <div dangerouslySetInnerHTML={{ __html: getPreviewContent().replace(/\n/g, '<br />') }} />
              ) : (
                getPreviewContent()
              )}
            </div>
            
            {/* Expand/Collapse button for long messages */}
            {content.length > 150 && !isExpanded && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs p-0"
                onClick={() => setIsExpanded(true)}
              >
                Show more
              </Button>
            )}
            
            {/* Metadata badges */}
            {metadata && (
              <div className="flex flex-wrap gap-1">
                {metadata.modality && (
                  <Badge variant="outline" className="text-xs">
                    {metadata.modality}
                  </Badge>
                )}
                {metadata.pluginId && (
                  <Badge variant="outline" className="text-xs">
                    Plugin: {metadata.pluginId}
                  </Badge>
                )}
                {metadata.artifactId && (
                  <Badge variant="outline" className="text-xs">
                    Artifact: {metadata.artifactId}
                  </Badge>
                )}
                {metadata.workflowId && (
                  <Badge variant="outline" className="text-xs">
                    Workflow: {metadata.workflowId}
                  </Badge>
                )}
                {metadata.confidence && (
                  <Badge 
                    variant="outline" 
                    className={cn(
                      "text-xs",
                      metadata.confidence > 0.8 ? "text-green-600" :
                      metadata.confidence > 0.5 ? "text-yellow-600" : "text-red-600"
                    )}
                  >
                    Confidence: {Math.round(metadata.confidence * 100)}%
                  </Badge>
                )}
              </div>
            )}
            
            {/* Debug info for expert users */}
            {showDebugInfo && (
              <div className="text-xs font-mono bg-muted p-2 rounded-md mt-2">
                <div>Message ID: {id}</div>
                {metadata?.memoryOps ? (
                  <div>Memory Ops: {JSON.stringify(metadata.memoryOps as Record<string, unknown>, null, 2)}</div>
                ) : null}
              </div>
            )}
            
            {/* Action buttons */}
            {(showActions || isMobile) && (
              <div className="message-actions">
                <div className="flex gap-1">
                  {/* Copy button */}
                  <button
                    className="message-action-button"
                    onClick={handleCopy}
                    title={isCopied ? "Copied!" : "Copy"}
                  >
                    {isCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </button>
                  
                  {/* Edit button (only for user messages) */}
                  {role === 'user' && (
                    <button
                      className="message-action-button"
                      onClick={() => setIsEditing(true)}
                      title="Edit"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                  )}
                  
                  {/* Retry button (only for assistant messages) */}
                  {role === 'assistant' && onRetry && (
                    <button
                      className="message-action-button"
                      onClick={() => onRetry(id)}
                      title="Retry"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  )}
                  
                  {/* Speech toggle button */}
                  {adaptationPolicy.enableSoundEffects && (
                    <button
                      className="message-action-button"
                      onClick={handleToggleSpeech}
                      title={isSpeaking ? "Stop speaking" : "Speak"}
                    >
                      {isSpeaking ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                    </button>
                  )}
                </div>
                
                {/* Feedback buttons (only for assistant messages) */}
                {role === 'assistant' && onFeedback && (
                  <div className="flex gap-1">
                    <button
                      className={cn(
                        "message-action-button",
                        feedback === 'positive' ? "bg-green-100 text-green-600" : ""
                      )}
                      onClick={() => handleFeedback(true)}
                      title="Helpful"
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </button>
                    <button
                      className={cn(
                        "message-action-button",
                        feedback === 'negative' ? "bg-red-100 text-red-600" : ""
                      )}
                      onClick={() => handleFeedback(false)}
                      title="Not helpful"
                    >
                      <ThumbsDown className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            )}
            
            {/* Suggested actions */}
            {showAdvancedFeatures && metadata?.actions && metadata.actions.length > 0 && (
              <div className="pt-2 space-y-1">
                <div className="text-xs font-medium">Suggested actions:</div>
                <div className="flex flex-wrap gap-1">
                  {metadata.actions.map((action) => (
                    <button
                      key={action.id}
                      className="action-button"
                      onClick={() => onExecuteAction?.(action.id)}
                    >
                      {action.title}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Guided mode tooltip for beginners */}
      {adaptationPolicy.guidedMode && role === 'assistant' && (
        <div className="guided-element absolute -top-8 left-0 text-xs bg-blue-500 text-white px-2 py-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
          Click the buttons below to interact with this message
        </div>
      )}
    </div>
  );
};
