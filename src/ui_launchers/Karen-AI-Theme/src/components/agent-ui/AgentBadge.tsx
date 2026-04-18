import React from 'react';
import { Agent } from '@/lib/agent-ui/service';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface AgentBadgeProps {
  agent: Agent;
  onClick?: (agent: Agent) => void;
  isActive?: boolean;
}

export function AgentBadge({ agent, onClick, isActive = false }: AgentBadgeProps) {
  const statusColors = {
    online: 'bg-green-500',
    offline: 'bg-gray-400',
    busy: 'bg-yellow-500'
  };

  return (
    <div 
      onClick={() => onClick && onClick(agent)}
      className={`
        flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer
        ${isActive ? 'border-primary bg-primary/10 shadow-sm' : 'border-border bg-card hover:border-primary/50 hover:bg-card/80'}
      `}
    >
      <div className="relative">
        <Avatar className="h-10 w-10 border shadow-sm">
          <AvatarImage src={agent.avatar} alt={agent.name} />
          <AvatarFallback className="bg-primary/20 text-primary font-medium">
            {agent.name.substring(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div 
          className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background ${statusColors[agent.status]}`} 
          title={agent.status}
        />
      </div>
      
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold truncate text-foreground">{agent.name}</h4>
        <p className="text-xs text-muted-foreground truncate" title={agent.description}>
          {agent.description}
        </p>
      </div>
    </div>
  );
}
