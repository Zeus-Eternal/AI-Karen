"use client";

import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileCode, Eye, Download, Copy, Check, X } from 'lucide-react';
import { CodeBlock } from '@/components/ui/syntax-highlighter';
import { cn } from '@/lib/utils';

export interface Artifact {
  id: string;
  type: 'code' | 'text' | 'data';
  title: string;
  content: string;
  language?: string;
  description?: string;
  status?: 'pending' | 'approved' | 'rejected';
}

export interface CopilotArtifactsProps {
  artifacts?: Artifact[];
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onDownload?: (id: string) => void;
  onCopy?: (id: string, content: string) => void;
  className?: string;
}

export default function CopilotArtifacts({
  artifacts = [],
  onApprove,
  onReject,
  onDownload,
  onCopy,
  className,
}: CopilotArtifactsProps) {
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const handleCopy = (id: string, content: string) => {
    if (onCopy) {
      onCopy(id, content);
    } else {
      navigator.clipboard.writeText(content);
    }
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (artifacts.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <FileCode className="h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-600 dark:text-gray-400">No artifacts generated yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <FileCode className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        <h3 className="text-lg font-semibold">Copilot Artifacts</h3>
        <Badge variant="secondary">{artifacts.length}</Badge>
      </div>

      <div className="space-y-3">
        {artifacts.map((artifact) => (
          <Card key={artifact.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-base">{artifact.title}</CardTitle>
                  {artifact.description && (
                    <CardDescription className="text-sm mt-1">
                      {artifact.description}
                    </CardDescription>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{artifact.type}</Badge>
                  {artifact.status === 'approved' && (
                    <Badge className="bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                      Approved
                    </Badge>
                  )}
                  {artifact.status === 'rejected' && (
                    <Badge className="bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
                      Rejected
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <Tabs defaultValue="preview" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="preview">
                    <Eye className="h-4 w-4 mr-2" />
                    Preview
                  </TabsTrigger>
                  <TabsTrigger value="code">
                    <FileCode className="h-4 w-4 mr-2" />
                    Code
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="preview" className="mt-4">
                  <div className="rounded-md bg-gray-50 dark:bg-gray-900 p-4">
                    {artifact.type === 'code' && artifact.language ? (
                      <CodeBlock
                        language={artifact.language}
                        theme="dark"
                        showLineNumbers
                        className="text-sm"
                      >
                        {artifact.content}
                      </CodeBlock>
                    ) : (
                      <pre className="text-sm whitespace-pre-wrap">
                        {artifact.content}
                      </pre>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="code" className="mt-4">
                  <div className="rounded-md bg-gray-900 p-4">
                    <pre className="text-sm text-gray-100 overflow-auto">
                      {artifact.content}
                    </pre>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>

            <CardFooter className="gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy(artifact.id, artifact.content)}
              >
                {copiedId === artifact.id ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    Copy
                  </>
                )}
              </Button>

              {onDownload && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDownload(artifact.id)}
                >
                  <Download className="h-3 w-3 mr-1" />
                  Download
                </Button>
              )}

              {artifact.status === 'pending' && (
                <>
                  {onApprove && (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => onApprove(artifact.id)}
                      className="ml-auto"
                    >
                      <Check className="h-3 w-3 mr-1" />
                      Approve
                    </Button>
                  )}
                  {onReject && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => onReject(artifact.id)}
                    >
                      <X className="h-3 w-3 mr-1" />
                      Reject
                    </Button>
                  )}
                </>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}

export { CopilotArtifacts };
export type { Artifact };
