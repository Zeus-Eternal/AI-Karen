import { AlertCircle, ServerCrash, CheckCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { Session } from '../types';

interface StatusIndicatorsProps {
  isBackendOffline: boolean;
  error: string | null;
  currentSession: Session | null;
}

export function StatusIndicators({ isBackendOffline, error, currentSession }: StatusIndicatorsProps) {
  return (
    <>
      {isBackendOffline && (
        <div className="bg-destructive/10 text-destructive border-b border-destructive/20 p-2 text-xs flex items-center justify-center gap-2 sticky top-0 z-10 backdrop-blur-sm shadow-sm ring-1 ring-destructive/20">
          <ServerCrash className="h-4 w-4 shrink-0" />
          <span>Backend services are currently unavailable or unreachable. Continuing in detached mode.</span>
        </div>
      )}

      {error && (
        <div className="bg-destructive/10 text-destructive border-b border-destructive/20 p-2 text-xs flex items-center justify-center gap-2 sticky top-0 z-10 backdrop-blur-sm shadow-sm ring-1 ring-destructive/20">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {currentSession && (
        <div className="bg-muted/50 border-b border-border p-2 text-xs flex items-center justify-center gap-2 sticky top-0 z-10 backdrop-blur-sm">
          <CheckCircle className="h-4 w-4 shrink-0 text-green-500" />
          <span>Session: {currentSession.title}</span>
          <Badge variant="outline" className="text-xs">
            {currentSession.messageCount} messages
          </Badge>
        </div>
      )}
    </>
  );
}