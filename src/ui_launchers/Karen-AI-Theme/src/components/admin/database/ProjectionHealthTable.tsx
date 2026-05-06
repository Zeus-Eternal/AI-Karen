import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCcw, CheckCircle2, AlertCircle, Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import { databaseOperationsApi, ProjectionHealth } from '@/lib/database-operations-api';
import { useToast } from '@/hooks/use-toast';

interface ProjectionHealthTableProps {
    projections: ProjectionHealth[];
}

export const ProjectionHealthTable: React.FC<ProjectionHealthTableProps> = ({ projections }) => {
    const [retrying, setRetrying] = useState<string | null>(null);
    const { toast } = useToast();

    const handleRetry = async () => {
        setRetrying('all');
        try {
            await databaseOperationsApi.retryProjections();
            toast({
                title: 'Retry Initiated',
                description: 'Projection sync retries have been triggered.',
            });
        } catch (err) {
            toast({
                title: 'Retry Failed',
                description: 'Failed to trigger projection retries.',
                variant: 'destructive',
            });
        } finally {
            setRetrying(null);
        }
    };

    if (projections.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-10 bg-muted/20 rounded-lg border border-dashed">
                <Clock className="w-8 h-8 text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">No active projections registered.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center">
                <p className="text-xs text-muted-foreground">
                    Projections maintain specialized views of memory across different storage tiers.
                </p>
                <Button 
                    size="sm" 
                    variant="outline" 
                    className="h-7 text-xs gap-1.5"
                    onClick={handleRetry}
                    disabled={retrying === 'all'}
                >
                    <RefreshCcw className={cn("w-3 h-3", retrying === 'all' && "animate-spin")} />
                    Retry All
                </Button>
            </div>

            <div className="border rounded-md overflow-hidden bg-background">
                <Table>
                    <TableHeader className="bg-muted/50">
                        <TableRow>
                            <TableHead className="text-[10px] uppercase font-bold tracking-wider">Projection</TableHead>
                            <TableHead className="text-[10px] uppercase font-bold tracking-wider">Target Tier</TableHead>
                            <TableHead className="text-[10px] uppercase font-bold tracking-wider">Status</TableHead>
                            <TableHead className="text-[10px] uppercase font-bold tracking-wider text-right">Lag</TableHead>
                            <TableHead className="text-[10px] uppercase font-bold tracking-wider text-right">Last Projected</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {projections.map((p) => (
                            <TableRow key={p.name} className="hover:bg-muted/30 transition-colors">
                                <TableCell className="font-medium text-xs">{p.name}</TableCell>
                                <TableCell>
                                    <Badge variant="outline" className="text-[9px] uppercase h-4 px-1">
                                        {p.target_tier}
                                    </Badge>
                                </TableCell>
                                <TableCell>
                                    <div className="flex items-center gap-1.5">
                                        {p.status === 'healthy' ? (
                                            <CheckCircle2 className="w-3 h-3 text-green-500" />
                                        ) : p.status === 'degraded' ? (
                                            <Clock className="w-3 h-3 text-yellow-500" />
                                        ) : (
                                            <AlertCircle className="w-3 h-3 text-destructive" />
                                        )}
                                        <span className={cn(
                                            "text-xs capitalize",
                                            p.status === 'healthy' ? "text-green-600" :
                                            p.status === 'degraded' ? "text-yellow-600" :
                                            "text-destructive"
                                        )}>
                                            {p.status}
                                        </span>
                                    </div>
                                </TableCell>
                                <TableCell className="text-right font-mono text-xs">
                                    {p.lag_count !== null ? (
                                        <span className={cn(
                                            (p.lag_count ?? 0) > 100 ? "text-destructive font-bold" : 
                                            (p.lag_count ?? 0) > 0 ? "text-yellow-600" : "text-muted-foreground"
                                        )}>
                                            {p.lag_count}
                                        </span>
                                    ) : '—'}
                                </TableCell>
                                <TableCell className="text-right text-xs text-muted-foreground">
                                    {p.last_projected_at ? new Date(p.last_projected_at).toLocaleTimeString() : 'Never'}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
            
            {(projections.some(p => p.status !== 'healthy')) && (
                <div className="bg-yellow-500/5 border border-yellow-500/10 p-2 rounded flex items-center gap-2 text-[10px] text-yellow-700 dark:text-yellow-400 italic">
                    <Zap className="w-3 h-3" />
                    Some projections are experiencing lag. System may return slightly stale data for complex queries.
                </div>
            )}
        </div>
    );
};
