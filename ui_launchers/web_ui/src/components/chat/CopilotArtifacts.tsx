'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Check, 
  X, 
  Copy, 
  Download, 
  Expand, 
  Minimize2,
  Code,
  FileText,
  GitBranch,
  Eye,
  EyeOff,
  ChevronRight,
  ChevronDown,
  AlertCircle,
  CheckCircle,
  Info,
  Zap,
  RefreshCw
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// Syntax highlighting (using a simple approach, could be enhanced with Prism.js or similar)
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Types for artifacts
export interface CopilotArtifact {
  id: string;
  type: 'code' | 'diff' | 'test' | 'documentation' | 'analysis' | 'suggestion';
  title: string;
  description?: string;
  content: string;
  language?: string;
  metadata?: {
    confidence?: number;
    complexity?: 'low' | 'medium' | 'high';
    impact?: 'low' | 'medium' | 'high';
    category?: string;
    tags?: string[];
    estimatedTime?: string;
    dependencies?: string[];
    warnings?: string[];
    suggestions?: string[];
  };
  actions?: ArtifactAction[];
  status?: 'pending' | 'approved' | 'rejected' | 'applied';
  timestamp: Date;
}

export interface ArtifactAction {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'destructive' | 'outline' | 'secondary';
  handler: () => void | Promise<void>;
  disabled?: boolean;
  tooltip?: string;
}

export interface DiffLine {
  type: 'added' | 'removed' | 'unchanged' | 'context';
  content: string;
  lineNumber?: number;
  oldLineNumber?: number;
  newLineNumber?: number;
}

export interface CopilotArtifactsProps {
  artifacts: CopilotArtifact[];
  onArtifactAction?: (artifactId: string, actionId: string) => void;
  onApprove?: (artifactId: string) => void;
  onReject?: (artifactId: string) => void;
  onApply?: (artifactId: string) => void;
  className?: string;
  theme?: 'light' | 'dark';
  maxHeight?: string;
  showLineNumbers?: boolean;
  enableCollapse?: boolean;
}

// Utility function to parse diff content
const parseDiff = (diffContent: string): DiffLine[] => {
  const lines = diffContent.split('\n');
  const parsedLines: DiffLine[] = [];
  let oldLineNumber = 1;
  let newLineNumber = 1;
  
  for (const line of lines) {
    if (line.startsWith('@@')) {
      // Diff header - extract line numbers
      const match = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/);
      if (match) {
        oldLineNumber = parseInt(match[1]);
        newLineNumber = parseInt(match[2]);
      }
      parsedLines.push({
        type: 'context',
        content: line,
        oldLineNumber,
        newLineNumber
      });
    } else if (line.startsWith('+')) {
      parsedLines.push({
        type: 'added',
        content: line.substring(1),
        newLineNumber: newLineNumber++
      });
    } else if (line.startsWith('-')) {
      parsedLines.push({
        type: 'removed',
        content: line.substring(1),
        oldLineNumber: oldLineNumber++
      });
    } else if (line.startsWith(' ') || line === '') {
      parsedLines.push({
        type: 'unchanged',
        content: line.substring(1) || line,
        oldLineNumber: oldLineNumber++,
        newLineNumber: newLineNumber++
      });
    } else {
      // Context line
      parsedLines.push({
        type: 'context',
        content: line,
        oldLineNumber,
        newLineNumber
      });
    }
  }
  
  return parsedLines;
};

// Individual artifact component
const ArtifactCard: React.FC<{
  artifact: CopilotArtifact;
  onAction?: (actionId: string) => void;
  onApprove?: () => void;
  onReject?: () => void;
  onApply?: () => void;
  theme?: 'light' | 'dark';
  showLineNumbers?: boolean;
  enableCollapse?: boolean;
}> = ({
  artifact,
  onAction,
  onApprove,
  onReject,
  onApply,
  theme = 'light',
  showLineNumbers = true,
  enableCollapse = true
}) => {
  const { toast } = useToast();
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState('content');
  
  // Parse diff if artifact is a diff type
  const diffLines = useMemo(() => {
    if (artifact.type === 'diff') {
      return parseDiff(artifact.content);
    }
    return [];
  }, [artifact.content, artifact.type]);
  
  // Handle copy to clipboard
  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
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
  }, [artifact.content, toast]);
  
  // Handle download
  const handleDownload = useCallback(() => {
    const blob = new Blob([artifact.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title.replace(/\s+/g, '_')}.${artifact.language || 'txt'}`;
    a.click();
    URL.revokeObjectURL(url);
  }, [artifact.content, artifact.title, artifact.language]);
  
  // Get artifact icon
  const getArtifactIcon = () => {
    switch (artifact.type) {
      case 'code':
        return Code;
      case 'diff':
        return GitBranch;
      case 'test':
        return CheckCircle;
      case 'documentation':
        return FileText;
      case 'analysis':
        return Zap;
      case 'suggestion':
        return Info;
      default:
        return FileText;
    }
  };
  
  const ArtifactIcon = getArtifactIcon();
  
  // Get status color
  const getStatusColor = () => {
    switch (artifact.status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'applied':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
  };
  
  // Render diff view
  const renderDiffView = () => (
    <div className="font-mono text-sm">
      {diffLines.map((line, index) => (
        <div
          key={index}
          className={`flex ${
            line.type === 'added' ? 'bg-green-50 text-green-900' :
            line.type === 'removed' ? 'bg-red-50 text-red-900' :
            line.type === 'context' ? 'bg-gray-50 text-gray-600' :
            ''
          }`}
        >
          {showLineNumbers && (
            <div className="flex-shrink-0 w-16 px-2 py-1 text-xs text-gray-500 border-r">
              <span className="inline-block w-6 text-right">
                {line.oldLineNumber || ''}
              </span>
              <span className="inline-block w-6 text-right ml-1">
                {line.newLineNumber || ''}
              </span>
            </div>
          )}
          <div className="flex-1 px-3 py-1 whitespace-pre-wrap">
            <span className={`inline-block w-4 ${
              line.type === 'added' ? 'text-green-600' :
              line.type === 'removed' ? 'text-red-600' :
              'text-gray-400'
            }`}>
              {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
            </span>
            {line.content}
          </div>
        </div>
      ))}
    </div>
  );
  
  // Render code view
  const renderCodeView = () => (
    <SyntaxHighlighter
      language={artifact.language || 'text'}
      style={theme === 'dark' ? oneDark : oneLight}
      showLineNumbers={showLineNumbers}
      customStyle={{
        margin: 0,
        borderRadius: '0.375rem',
        fontSize: '0.875rem'
      }}
    >
      {artifact.content}
    </SyntaxHighlighter>
  );
  
  // Render metadata
  const renderMetadata = () => {
    if (!artifact.metadata) return null;
    
    return (
      <div className="space-y-3">
        {/* Confidence and Impact */}
        <div className="flex gap-4">
          {artifact.metadata.confidence && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Confidence:</span>
              <Badge variant="outline">
                {Math.round(artifact.metadata.confidence * 100)}%
              </Badge>
            </div>
          )}
          {artifact.metadata.impact && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Impact:</span>
              <Badge 
                variant={
                  artifact.metadata.impact === 'high' ? 'destructive' :
                  artifact.metadata.impact === 'medium' ? 'default' :
                  'secondary'
                }
              >
                {artifact.metadata.impact}
              </Badge>
            </div>
          )}
        </div>
        
        {/* Tags */}
        {artifact.metadata.tags && artifact.metadata.tags.length > 0 && (
          <div>
            <span className="text-sm font-medium mb-2 block">Tags:</span>
            <div className="flex flex-wrap gap-1">
              {artifact.metadata.tags.map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        {/* Warnings */}
        {artifact.metadata.warnings && artifact.metadata.warnings.length > 0 && (
          <div>
            <span className="text-sm font-medium mb-2 block text-amber-700">Warnings:</span>
            <div className="space-y-1">
              {artifact.metadata.warnings.map((warning, index) => (
                <div key={index} className="flex items-start gap-2 text-sm text-amber-700">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  {warning}
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Suggestions */}
        {artifact.metadata.suggestions && artifact.metadata.suggestions.length > 0 && (
          <div>
            <span className="text-sm font-medium mb-2 block text-blue-700">Suggestions:</span>
            <div className="space-y-1">
              {artifact.metadata.suggestions.map((suggestion, index) => (
                <div key={index} className="flex items-start gap-2 text-sm text-blue-700">
                  <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  {suggestion}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };
  
  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <ArtifactIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <CardTitle className="text-base">{artifact.title}</CardTitle>
                {artifact.status && (
                  <Badge className={`text-xs ${getStatusColor()}`}>
                    {artifact.status}
                  </Badge>
                )}
              </div>
              {artifact.description && (
                <p className="text-sm text-muted-foreground">
                  {artifact.description}
                </p>
              )}
            </div>
          </div>
          
          {/* Action buttons */}
          <div className="flex items-center gap-1 ml-4">
            {enableCollapse && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="h-8 w-8 p-0"
              >
                {isExpanded ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Expand className="h-4 w-4" />
                )}
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="h-8 w-8 p-0"
            >
              <Copy className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="h-8 w-8 p-0"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="pt-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="metadata">Details</TabsTrigger>
            </TabsList>
            
            <TabsContent value="content" className="mt-4">
              <ScrollArea className="max-h-96 w-full rounded-md border">
                {artifact.type === 'diff' ? renderDiffView() : renderCodeView()}
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="metadata" className="mt-4">
              {renderMetadata()}
            </TabsContent>
          </Tabs>
          
          {/* Action buttons */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <div className="flex gap-2">
              {/* Custom actions */}
              {artifact.actions?.map((action) => (
                <Button
                  key={action.id}
                  variant={action.variant || 'outline'}
                  size="sm"
                  onClick={action.handler}
                  disabled={action.disabled}
                  title={action.tooltip}
                >
                  <action.icon className="h-4 w-4 mr-2" />
                  {action.label}
                </Button>
              ))}
            </div>
            
            {/* Standard approval actions */}
            <div className="flex gap-2">
              {onReject && artifact.status === 'pending' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onReject}
                >
                  <X className="h-4 w-4 mr-2" />
                  Reject
                </Button>
              )}
              
              {onApprove && artifact.status === 'pending' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onApprove}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              )}
              
              {onApply && (artifact.status === 'approved' || artifact.status === 'pending') && (
                <Button
                  size="sm"
                  onClick={onApply}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Apply Changes
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
};

// Main artifacts container component
export const CopilotArtifacts: React.FC<CopilotArtifactsProps> = ({
  artifacts,
  onArtifactAction,
  onApprove,
  onReject,
  onApply,
  className = '',
  theme = 'light',
  maxHeight = '600px',
  showLineNumbers = true,
  enableCollapse = true
}) => {
  const [expandedArtifacts, setExpandedArtifacts] = useState<Set<string>>(new Set());
  
  // Handle artifact actions
  const handleArtifactAction = useCallback((artifactId: string, actionId: string) => {
    if (onArtifactAction) {
      onArtifactAction(artifactId, actionId);
    }
  }, [onArtifactAction]);
  
  // Toggle expand/collapse all
  const toggleExpandAll = useCallback(() => {
    if (expandedArtifacts.size === artifacts.length) {
      setExpandedArtifacts(new Set());
    } else {
      setExpandedArtifacts(new Set(artifacts.map(a => a.id)));
    }
  }, [artifacts, expandedArtifacts.size]);
  
  if (artifacts.length === 0) {
    return null;
  }
  
  return (
    <div className={`copilot-artifacts space-y-4 ${className}`} style={{ maxHeight }}>
      {/* Header with controls */}
      {artifacts.length > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium">
            {artifacts.length} Copilot Artifact{artifacts.length > 1 ? 's' : ''}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleExpandAll}
          >
            {expandedArtifacts.size === artifacts.length ? (
              <>
                <EyeOff className="h-4 w-4 mr-2" />
                Collapse All
              </>
            ) : (
              <>
                <Eye className="h-4 w-4 mr-2" />
                Expand All
              </>
            )}
          </Button>
        </div>
      )}
      
      {/* Artifacts list */}
      <ScrollArea className="w-full" style={{ maxHeight }}>
        <div className="space-y-4">
          {artifacts.map((artifact) => (
            <ArtifactCard
              key={artifact.id}
              artifact={artifact}
              onAction={(actionId) => handleArtifactAction(artifact.id, actionId)}
              onApprove={onApprove ? () => onApprove(artifact.id) : undefined}
              onReject={onReject ? () => onReject(artifact.id) : undefined}
              onApply={onApply ? () => onApply(artifact.id) : undefined}
              theme={theme}
              showLineNumbers={showLineNumbers}
              enableCollapse={enableCollapse}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

export default CopilotArtifacts;