import React from 'react';
import { CheckCircle2, Circle, Clock, AlertCircle, PlayCircle, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TraceEvent, ExecutionStatus } from '@/lib/types';

interface AgentTraceTimelineProps {
  trace: TraceEvent[];
  compact?: boolean;
}

const statusIcons: Record<ExecutionStatus, React.ReactNode> = {
  pending: <Circle className="w-3 h-3 text-muted-foreground" />,
  running: <PlayCircle className="w-3 h-3 text-primary animate-pulse" />,
  completed: <CheckCircle2 className="w-3 h-3 text-green-500" />,
  failed: <AlertCircle className="w-3 h-3 text-destructive" />,
  skipped: <Circle className="w-3 h-3 text-muted-foreground/50" />,
  blocked: <Clock className="w-3 h-3 text-yellow-500" />,
  requires_approval: <Clock className="w-3 h-3 text-yellow-500" />,
  scheduled: <Calendar className="w-3 h-3 text-blue-500" />,
  cancelled: <Circle className="w-3 h-3 text-muted-foreground" />,
  requires_confirmation: <Clock className="w-3 h-3 text-yellow-500" />,
};

export const AgentTraceTimeline: React.FC<AgentTraceTimelineProps> = ({ trace, compact }) => {
  if (!trace || trace.length === 0) return null;

  return (
    <div className={cn("space-y-2 my-2", compact ? "opacity-80 scale-95" : "")}>
      <div className="flex items-center gap-2 mb-1">
        <div className="h-px bg-border flex-1" />
        <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Execution Trace</span>
        <div className="h-px bg-border flex-1" />
      </div>
      <div className="relative pl-4 space-y-3 before:absolute before:left-1.5 before:top-1.5 before:bottom-1.5 before:w-px before:bg-border">
        {trace.map((event, index) => (
          <div key={event.id || index} className="relative group">
            <div className="absolute -left-[1.375rem] top-1 bg-background p-0.5 rounded-full z-10">
              {statusIcons[event.status] || <Circle className="w-3 h-3 text-muted-foreground" />}
            </div>
            <div className="flex flex-col">
              <div className="flex justify-between items-baseline gap-4">
                <span className={cn(
                  "text-xs font-medium",
                  event.status === 'running' ? "text-primary" : "text-foreground"
                )}>
                  {event.label || event.type.replace(/_/g, ' ')}
                </span>
                {event.latency_ms && (
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                    {event.latency_ms.toFixed(0)}ms
                  </span>
                )}
              </div>
              {event.metadata?.message && (
                <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">
                  {String(event.metadata.message)}
                </p>
              )}
              {event.error && (
                <p className="text-[10px] text-destructive mt-0.5 font-medium italic">
                  {event.error}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
