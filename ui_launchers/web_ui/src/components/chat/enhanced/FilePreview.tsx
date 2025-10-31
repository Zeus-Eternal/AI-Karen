'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  File,
  Image,
  Code,
  FileText,
  Download,
  Eye,
  X,
  Maximize2,
  Copy,
  Search,
  Zap
} from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTheme } from 'next-themes';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Attachment, AttachmentAnalysis } from '@/types/enhanced-chat';

interface FilePreviewProps {
  attachment: Attachment;
  onClose?: () => void;
  onAnalyze?: (attachment: Attachment) => Promise<AttachmentAnalysis>;
  className?: string;
  compact?: boolean;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  attachment,
  onClose,
  onAnalyze,
  className = '',
  compact = false
}) => {
  const { theme } = useTheme();
  const { toast } = useToast();
  const [fileContent, setFileContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<AttachmentAnalysis | undefined>(attachment.analysis);

  // Load file content for text-based files
  useEffect(() => {
    const loadFileContent = async () => {
      if (attachment.type === 'code' || attachment.type === 'document') {
        setIsLoading(true);
        try {
          if (attachment.analysis?.extractedText) {
            setFileContent(attachment.analysis.extractedText);
          } else {
            // Simulate loading file content
            const response = await fetch(attachment.url);
            const text = await response.text();
            setFileContent(text);
          }
        } catch (error) {
          console.error('Failed to load file content:', error);
          setFileContent('Failed to load file content');
        } finally {
          setIsLoading(false);
        }
      }
    };

    loadFileContent();
  }, [attachment]);

  // Get programming language from file extension
  const getLanguageFromExtension = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    const languageMap: Record<string, string> = {
      'js': 'javascript',
      'jsx': 'jsx',
      'ts': 'typescript',
      'tsx': 'tsx',
      'py': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'xml': 'xml',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'sql': 'sql',
      'php': 'php',
      'rb': 'ruby',
      'go': 'go',
      'rs': 'rust',
      'sh': 'bash'
    };
    return languageMap[extension || ''] || 'text';
  };

  // Handle file analysis
  const handleAnalyze = async () => {
    if (!onAnalyze) return;
    
    setIsAnalyzing(true);
    try {
      const newAnalysis = await onAnalyze(attachment);
      setAnalysis(newAnalysis);
      toast({
        title: 'Analysis Complete',
        description: 'File has been analyzed successfully'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Analysis Failed',
        description: 'Failed to analyze file content'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Copy content to clipboard
  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: 'Copied',
        description: 'Content copied to clipboard'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy to clipboard'
      });
    }
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Render image preview
  const renderImagePreview = () => (
    <div className="space-y-4">
      <div className="relative">
        <img
          src={attachment.url}
          alt={attachment.name}
          className="w-full h-auto max-h-96 object-contain rounded-lg border"
        />
        {attachment.metadata?.dimensions && (
          <Badge className="absolute top-2 right-2 bg-black/50 text-white">
            {attachment.metadata.dimensions.width} × {attachment.metadata.dimensions.height}
          </Badge>
        )}
      </div>
      
      {analysis?.extractedText && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Extracted Text</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-32">
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {analysis.extractedText}
              </p>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  );

  // Render code preview
  const renderCodePreview = () => {
    const language = getLanguageFromExtension(attachment.name);
    
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="outline">{language}</Badge>
            <span className="text-sm text-muted-foreground">
              {fileContent.split('\n').length} lines
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => copyToClipboard(fileContent)}
          >
            <Copy className="h-4 w-4 mr-2" />
            Copy
          </Button>
        </div>
        
        <Card>
          <CardContent className="p-0">
            <ScrollArea className="h-96">
              <SyntaxHighlighter
                language={language}
                style={theme === 'dark' ? oneDark : oneLight}
                customStyle={{
                  margin: 0,
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem'
                }}
                showLineNumbers
                wrapLines
              >
                {fileContent}
              </SyntaxHighlighter>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    );
  };

  // Render document preview
  const renderDocumentPreview = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Badge variant="outline">{attachment.mimeType}</Badge>
        <Button
          variant="outline"
          size="sm"
          onClick={() => copyToClipboard(fileContent)}
        >
          <Copy className="h-4 w-4 mr-2" />
          Copy
        </Button>
      </div>
      
      <Card>
        <CardContent className="p-4">
          <ScrollArea className="h-96">
            <div className="prose prose-sm max-w-none">
              <pre className="whitespace-pre-wrap text-sm">
                {fileContent}
              </pre>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );

  // Render analysis panel
  const renderAnalysis = () => {
    if (!analysis) {
      return (
        <div className="text-center py-8">
          <Search className="h-8 w-8 mx-auto mb-4 opacity-50" />
          <p className="text-sm text-muted-foreground mb-4">
            No analysis available for this file
          </p>
          {onAnalyze && (
            <Button onClick={handleAnalyze} disabled={isAnalyzing}>
              <Zap className="h-4 w-4 mr-2" />
              {isAnalyzing ? 'Analyzing...' : 'Analyze File'}
            </Button>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {analysis.summary && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{analysis.summary}</p>
              {analysis.confidence && (
                <Badge variant="secondary" className="mt-2">
                  {Math.round(analysis.confidence * 100)}% confidence
                </Badge>
              )}
            </CardContent>
          </Card>
        )}

        {analysis.entities && analysis.entities.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Detected Entities</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {analysis.entities.map((entity, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {entity}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {analysis.topics && analysis.topics.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Topics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {analysis.topics.map((topic, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {topic}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {analysis.sentiment && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Sentiment</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge 
                variant={
                  analysis.sentiment === 'positive' ? 'default' :
                  analysis.sentiment === 'negative' ? 'destructive' : 'secondary'
                }
              >
                {analysis.sentiment}
              </Badge>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  if (compact) {
    return (
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="ghost" size="sm">
            <Eye className="h-4 w-4" />
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <File className="h-5 w-5" />
              {attachment.name}
            </DialogTitle>
          </DialogHeader>
          <FilePreview attachment={attachment} onAnalyze={onAnalyze} />
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <File className="h-5 w-5" />
            {attachment.name}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline">{attachment.type}</Badge>
            <span className="text-sm text-muted-foreground">
              {formatFileSize(attachment.size)}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const a = document.createElement('a');
                a.href = attachment.url;
                a.download = attachment.name;
                a.click();
              }}
            >
              <Download className="h-4 w-4" />
            </Button>
            
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0">
        <Tabs defaultValue="preview" className="h-full flex flex-col">
          <TabsList className="mx-4">
            <TabsTrigger value="preview">Preview</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <div className="flex-1 mt-4">
            <TabsContent value="preview" className="h-full m-0 px-4 pb-4">
              <ScrollArea className="h-full">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <>
                    {attachment.type === 'image' && renderImagePreview()}
                    {attachment.type === 'code' && renderCodePreview()}
                    {attachment.type === 'document' && renderDocumentPreview()}
                    {(attachment.type === 'video' || attachment.type === 'audio') && (
                      <div className="text-center py-8">
                        <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p className="text-sm text-muted-foreground">
                          Preview not available for {attachment.type} files
                        </p>
                      </div>
                    )}
                  </>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="analysis" className="h-full m-0 px-4 pb-4">
              <ScrollArea className="h-full">
                {renderAnalysis()}
              </ScrollArea>
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default FilePreview;