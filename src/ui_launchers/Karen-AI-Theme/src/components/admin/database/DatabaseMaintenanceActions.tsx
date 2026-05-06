import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Wrench, Sparkles, RefreshCw, Trash2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { databaseOperationsApi } from '@/lib/database-operations-api';
import { useToast } from '@/hooks/use-toast';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface DatabaseMaintenanceActionsProps {
    actions: string[];
}

export const DatabaseMaintenanceActions: React.FC<DatabaseMaintenanceActionsProps> = ({ actions }) => {
    const [executing, setExecuting] = useState<string | null>(null);
    const { toast } = useToast();

    const handleAction = async (action: string) => {
        setExecuting(action);
        try {
            if (action === 'maintenance.run') {
                await databaseOperationsApi.runMaintenance();
                toast({
                    title: 'Maintenance Started',
                    description: 'Full database optimization background task initiated.',
                });
            }
            // Add other actions as needed
        } catch (err) {
            toast({
                title: 'Action Failed',
                description: 'Failed to trigger maintenance task.',
                variant: 'destructive',
            });
        } finally {
            setExecuting(null);
        }
    };

    return (
        <Card className="shadow-sm">
            <CardHeader className="bg-muted/30 pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Wrench className="w-4 h-4 text-primary" />
                    Operational Controls
                </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-2">
                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button 
                            variant="outline" 
                            size="sm" 
                            className="w-full justify-start text-xs font-medium"
                            disabled={!actions.includes('maintenance.run') || executing === 'maintenance.run'}
                        >
                            <Sparkles className={cn("w-3.5 h-3.5 mr-2 text-primary", executing === 'maintenance.run' && "animate-spin")} />
                            Run Full Maintenance
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Run Full Maintenance?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This will trigger VACUUM, ANALYZE, and index optimization across all storage tiers. 
                                It may cause temporary latency spikes in chat responses.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleAction('maintenance.run')}>
                                Proceed
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>

                <Button variant="outline" size="sm" className="w-full justify-start text-xs font-medium">
                    <RefreshCw className="w-3.5 h-3.5 mr-2 text-primary" />
                    Repair Memory Indices
                </Button>

                <Button variant="outline" size="sm" className="w-full justify-start text-xs font-medium text-destructive hover:text-destructive hover:bg-destructive/5">
                    <Trash2 className="w-3.5 h-3.5 mr-2" />
                    Clear Cache Layers
                </Button>
                
                <div className="pt-2">
                    <div className="flex items-center gap-2 p-2 bg-blue-500/5 border border-blue-500/10 rounded text-[10px] text-blue-600 dark:text-blue-400">
                        <AlertCircle className="w-3 h-3" />
                        Actions are audited and require admin permissions.
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
