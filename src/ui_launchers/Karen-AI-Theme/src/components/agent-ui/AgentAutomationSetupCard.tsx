import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Calendar, Shield, Cpu, Tool, Database, Bell } from 'lucide-react';
import type { AutomationMetadata } from '@/lib/types';

interface AgentAutomationSetupCardProps {
  metadata: AutomationMetadata;
  onConfirm?: (draftId: string) => Promise<void>;
  onEdit?: (draftId: string) => void;
  onCancel?: (draftId: string) => Promise<void>;
}

export const AgentAutomationSetupCard: React.FC<AgentAutomationSetupCardProps> = ({
  metadata,
  onConfirm,
  onEdit,
  onCancel,
}) => {
  const draft = metadata.draft;
  if (!draft) return null;

  return (
    <Card className="my-4 border-primary/20 bg-background/50 backdrop-blur-sm overflow-hidden">
      <CardHeader className="bg-primary/5 pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Cpu className="w-4 h-4 text-primary" />
            Agent Automation Setup
          </CardTitle>
          <Badge variant={draft.risk_level === 'high' ? 'destructive' : 'outline'}>
            {draft.risk_level.toUpperCase()} RISK
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-4 space-y-4 text-sm">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground uppercase font-medium">Name</label>
            <p className="font-medium">{draft.name}</p>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground uppercase font-medium">Trigger</label>
            <p className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {draft.trigger.type === 'manual' ? 'Manual Run' : draft.trigger.schedule}
            </p>
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-xs text-muted-foreground uppercase font-medium">Goal</label>
          <p className="text-xs">{draft.goal}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground uppercase font-medium">Agent</label>
            <p>{draft.execution.agent_name || draft.execution.agent_id}</p>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground uppercase font-medium">Tools</label>
            <p className="text-xs">
              {draft.execution.tools.length > 0 
                ? draft.execution.tools.map((t: any) => t.name).join(', ')
                : 'None'}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 pt-2 border-t border-border/50">
          <div className="flex items-center gap-1 text-[10px] bg-secondary/30 px-2 py-1 rounded">
            <Database className="w-3 h-3" />
            Memory: {draft.memory.write_mode}
          </div>
          <div className="flex items-center gap-1 text-[10px] bg-secondary/30 px-2 py-1 rounded">
            <Shield className="w-3 h-3" />
            Approval: {draft.approval.required_before_execution ? 'Required' : 'Auto'}
          </div>
          <div className="flex items-center gap-1 text-[10px] bg-secondary/30 px-2 py-1 rounded">
            <Bell className="w-3 h-3" />
            Notify: {draft.notification.channels.join(', ')}
          </div>
        </div>

        {draft.warnings?.length > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 p-2 rounded flex gap-2 items-start">
            <AlertCircle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
            <div className="text-[10px] text-yellow-600 dark:text-yellow-400">
              {draft.warnings.map((w: string, i: number) => <div key={i}>{w}</div>)}
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="bg-primary/5 flex gap-2 pt-4">
        <Button 
          size="sm" 
          className="flex-1"
          onClick={() => onConfirm?.(draft.draft_id)}
        >
          Create Automation
        </Button>
        <Button 
          size="sm" 
          variant="outline"
          onClick={() => onEdit?.(draft.draft_id)}
        >
          Edit
        </Button>
        <Button 
          size="sm" 
          variant="ghost"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
          onClick={() => onCancel?.(draft.draft_id)}
        >
          Cancel
        </Button>
      </CardFooter>
    </Card>
  );
};
