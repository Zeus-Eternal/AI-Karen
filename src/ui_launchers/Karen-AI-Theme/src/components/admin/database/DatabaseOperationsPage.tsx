import React, { useEffect, useState, useCallback } from 'react';
import { databaseOperationsApi, DatabaseOperationsOverview } from '@/lib/database-operations-api';
import { StorageTierCards } from './StorageTierCards';
import { MemoryWritebackStatus } from './MemoryWritebackStatus';
import { ProjectionHealthTable } from './ProjectionHealthTable';
import { MigrationStatusCard } from './MigrationStatusCard';
import { DatabaseCircuitBreakerPanel } from './DatabaseCircuitBreakerPanel';
import { DatabaseMaintenanceActions } from './DatabaseMaintenanceActions';
import { DatabaseOperationsEmptyState } from './DatabaseOperationsEmptyState';
import { DatabaseOperationsErrorState } from './DatabaseOperationsErrorState';
import { useToast } from '@/hooks/use-toast';
import { Loader2, RefreshCw, Database, ShieldAlert, Activity } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export const DatabaseOperationsPage: React.FC = () => {
    const [overview, setOverview] = useState<DatabaseOperationsOverview | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { toast } = useToast();

    const fetchOverview = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await databaseOperationsApi.getOverview();
            setOverview(data);
        } catch (err: unknown) {
            console.error('Failed to fetch database operations overview:', err);
            setError(err instanceof Error ? err.message : 'Failed to connect to the database operations service');
            toast({
                title: 'Operational Error',
                description: 'Could not reach the database health service.',
                variant: 'destructive',
            });
        } finally {
            setIsLoading(false);
        }
    }, [toast]);

    useEffect(() => {
        fetchOverview();
    }, [fetchOverview]);

    if (isLoading && !overview) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <p className="text-muted-foreground animate-pulse">Syncing storage tier truth...</p>
            </div>
        );
    }

    if (error) {
        return <DatabaseOperationsErrorState error={error} onRetry={fetchOverview} />;
    }

    if (!overview) {
        return <DatabaseOperationsEmptyState onRetry={fetchOverview} />;
    }

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
                        <Database className="w-6 h-6 text-primary" />
                        Database Operations
                    </h1>
                    <p className="text-muted-foreground text-sm max-w-2xl">
                        Operational view of Karen&apos;s storage tiers, memory writeback state, and projection health.
                        Status derived from backend service health APIs.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant={overview.status === 'healthy' ? 'outline' : 'destructive'} className="h-6">
                        {overview.status.toUpperCase()}
                    </Badge>
                    <Button variant="outline" size="sm" onClick={fetchOverview} disabled={isLoading}>
                        <RefreshCw className={overview ? "w-4 h-4 mr-2" : "w-4 h-4 mr-2 animate-spin"} />
                        Refresh
                    </Button>
                </div>
            </div>

            {overview.warnings.length > 0 && (
                <div className="space-y-2">
                    {overview.warnings.map((warning, i) => (
                        <Alert key={i} variant="destructive" className="bg-destructive/5 border-destructive/20">
                            <ShieldAlert className="h-4 w-4" />
                            <AlertTitle>Operational Warning</AlertTitle>
                            <AlertDescription className="text-xs">{warning}</AlertDescription>
                        </Alert>
                    ))}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <section>
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Activity className="w-4 h-4 text-primary" />
                            Storage Tiers
                        </h2>
                        <StorageTierCards tiers={overview.storage_tiers} />
                    </section>

                    <Tabs defaultValue="projections" className="w-full">
                        <TabsList className="grid w-full grid-cols-3 mb-4">
                            <TabsTrigger value="projections">Projections</TabsTrigger>
                            <TabsTrigger value="writeback">Memory Writeback</TabsTrigger>
                            <TabsTrigger value="circuit-breakers">Circuit Breakers</TabsTrigger>
                        </TabsList>
                        <TabsContent value="projections" className="space-y-4">
                            <ProjectionHealthTable projections={overview.projections} />
                        </TabsContent>
                        <TabsContent value="writeback">
                            <MemoryWritebackStatus status={overview.memory_writeback} />
                        </TabsContent>
                        <TabsContent value="circuit-breakers">
                            <DatabaseCircuitBreakerPanel tiers={overview.storage_tiers} />
                        </TabsContent>
                    </Tabs>
                </div>

                <div className="space-y-6">
                    <MigrationStatusCard migrations={overview.migrations} />
                    <DatabaseMaintenanceActions actions={overview.actions_available} />
                    
                    <Card className="bg-muted/30 border-dashed">
                        <CardContent className="pt-6 text-xs text-muted-foreground space-y-2">
                            <div className="flex justify-between">
                                <span>Request ID</span>
                                <span className="font-mono">{overview.request_id}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Correlation ID</span>
                                <span className="font-mono">{overview.correlation_id}</span>
                            </div>
                            <div className="flex justify-between">
                                <span>Generated At</span>
                                <span>{new Date(overview.generated_at).toLocaleString()}</span>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};
