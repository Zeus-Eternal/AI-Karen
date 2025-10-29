'use client';

import { useEffect } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function ChatError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Chat page error:', error);
  }, [error]);

  const handleGoHome = () => {
    window.location.href = '/';
  };

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-destructive/50">
        <CardHeader>
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-8 w-8 text-destructive" />
            <div>
              <CardTitle className="text-xl">Chat Loading Error</CardTitle>
              <CardDescription className="mt-1">
                Failed to load the chat interface
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-sm font-medium text-destructive">
              {error.message.includes('ChunkLoadError') 
                ? 'Failed to load application resources. This might be due to a development server restart.'
                : error.message
              }
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <Button onClick={reset} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            
            <Button variant="outline" onClick={handleReload} className="w-full">
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload Page
            </Button>
            
            <Button variant="outline" onClick={handleGoHome} className="w-full">
              <Home className="h-4 w-4 mr-2" />
              Go Home
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            <p>
              If this error persists, try restarting the development server.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}