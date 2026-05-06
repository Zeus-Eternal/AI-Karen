import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Database, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MemoryWritebackHealth } from '@/lib/database-operations-api';

interface MemoryWritebackStatusProps {
    status: MemoryWritebackHealth;
}

export const MemoryWritebackStatus: React.FC<MemoryWritebackStatusProps> = ({ status }) => {
    return (
        <Card className="border-border/40 shadow-none bg-muted/10">
            <CardContent className="pt-6 space-y-6">
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "p-2 rounded-full",
                            status.status === 'healthy' ? "bg-green-500/10 text-green-500" : "bg-yellow-500/10 text-yellow-500"
                        )}>
                            <Database className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-sm font-semibold">Writeback Queue</h3>
                            <p className="text-xs text-muted-foreground">Background persistence of episodic memory</p>
                        </div>
                    </div>
                    <Badge variant={status.enabled ? "default" : "secondary"}>
                        {status.enabled ? 'ACTIVE' : 'DISABLED'}
                    </Badge>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-background border rounded-lg p-3 space-y-1 shadow-sm">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Queue Depth</span>
                        <p className="text-xl font-mono">{status.queue_depth ?? 0}</p>
                    </div>
                    <div className="bg-background border rounded-lg p-3 space-y-1 shadow-sm">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Pending</span>
                        <p className="text-xl font-mono text-primary">{status.pending_count ?? 0}</p>
                    </div>
                    <div className="bg-background border rounded-lg p-3 space-y-1 shadow-sm">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Failed</span>
                        <p className={cn("text-xl font-mono", (status.failed_count ?? 0) > 0 ? "text-destructive" : "text-green-500")}>
                            {status.failed_count ?? 0}
                        </p>
                    </div>
                    <div className="bg-background border rounded-lg p-3 space-y-1 shadow-sm">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold">Last Run</span>
                        <p className="text-xs truncate font-medium">
                            {status.last_write_at ? new Date(status.last_write_at).toLocaleTimeString() : 'Never'}
                        </p>
                    </div>
                </div>

                {status.degraded_reason && (
                    <div className="flex items-start gap-2 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 p-3 rounded-md text-xs border border-yellow-500/20">
                        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                        <p>{status.degraded_reason}</p>
                    </div>
                )}

                <div className="flex items-center gap-2 text-xs text-muted-foreground justify-center pt-2">
                    <Clock className="w-3 h-3" />
                    <span>Worker Status: <span className="font-medium text-foreground">{status.writeback_status || 'Idle'}</span></span>
                    {status.status === 'healthy' && (
                        <span className="flex items-center gap-1 text-green-500 ml-2">
                            <CheckCircle2 className="w-3 h-3" />
                            All clear
                        </span>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};
