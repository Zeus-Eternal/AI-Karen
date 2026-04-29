import { AlertCircle, CheckCircle, WifiOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { Session } from '../types';

interface StatusIndicatorsProps {
  isBackendOffline: boolean;
  error: string | null;
  currentSession: Session | null;
  isLoading?: boolean;
}

export function StatusIndicators({ isBackendOffline, error, currentSession, isLoading }: StatusIndicatorsProps) {
  return (
    <>
      {isBackendOffline && (
        <div className="bg-destructive/10 text-destructive border-b border-destructive/20 p-3 text-sm flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm shadow-sm ring-1 ring-destructive/20 animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-3">
            <WifiOff className="h-5 w-5 shrink-0 animate-pulse" />
            <div className="flex flex-col gap-1">
              <span className="font-medium">Backend Connection Lost</span>
              <span className="text-xs opacity-90">Operating in offline mode with limited functionality</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => window.location.reload()}
              className="px-3 py-1 text-xs bg-destructive/20 hover:bg-destructive/30 rounded-md transition-colors"
              aria-label="Retry connection"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-destructive/10 text-destructive border-b border-destructive/20 p-3 text-sm flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm shadow-sm ring-1 ring-destructive/20 animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 shrink-0 animate-bounce" />
            <div className="flex flex-col gap-1">
              <span className="font-medium">Error Occurred</span>
              <span className="text-xs opacity-90">{error}</span>
            </div>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1 text-xs bg-destructive/20 hover:bg-destructive/30 rounded-md transition-colors"
            aria-label="Reload page to recover from error"
          >
            Reload
          </button>
        </div>
      )}



      {currentSession && currentSession.messageCount === 0 && !isLoading && (
        <div className="bg-muted/50 border-b border-border p-3 text-sm flex items-center justify-center gap-3 sticky top-0 z-10 backdrop-blur-sm">
          <CheckCircle className="h-5 w-5 shrink-0 text-green-500" />
          <div className="flex flex-col items-center gap-1">
            <span className="font-medium">{currentSession.title || 'New Conversation'}</span>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {currentSession.messageCount} messages
              </Badge>
              <span className="text-xs opacity-70">
                Start chatting with Karen
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}