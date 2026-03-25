'use client';

import React, { useEffect, useState } from 'react';
import { useAgentStore } from '@/lib/agent-ui/store';
import { AgentBadge } from './AgentBadge';
import { Agent } from '@/lib/agent-ui/service';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';

interface AgentListProps {
  onSelect?: (agent: Agent) => void;
  selectedAgentId?: string;
  className?: string;
}

export function AgentList({ onSelect, selectedAgentId, className = '' }: AgentListProps) {
  const { agents, loading, error, fetchAgents } = useAgentStore();
  const [init, setInit] = useState(false);

  useEffect(() => {
    if (!init) {
      fetchAgents();
      setInit(true);
    }
  }, [init, fetchAgents]);

  const agentValues = Object.values(agents);
  const isLoading = loading.agents && agentValues.length === 0;

  return (
    <div className={`flex flex-col h-full bg-background border-r ${className}`}>
      <div className="p-4 border-b">
        <h3 className="font-semibold text-lg tracking-tight">Available Agents</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Select an AI assistant to start a conversation.
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {error.agents && (
            <Alert variant="destructive">
              <AlertDescription>{error.agents}</AlertDescription>
            </Alert>
          )}

          {isLoading ? (
            // Loading Skeletons
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-3/4" />
                </div>
              </div>
            ))
          ) : (
            agentValues.map((agent) => (
              <AgentBadge
                key={agent.id}
                agent={agent}
                isActive={agent.id === selectedAgentId}
                onClick={onSelect}
              />
            ))
          )}

          {!isLoading && agentValues.length === 0 && !error.agents && (
            <div className="text-center p-8 text-muted-foreground">
              No agents available offline.
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
