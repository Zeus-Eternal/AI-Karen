import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { History, FileSearch, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import { databaseOperationsApi, MigrationHealth } from '@/lib/database-operations-api';
import { useToast } from '@/hooks/use-toast';

interface MigrationStatusCardProps {
    migrations: MigrationHealth;
}

export const MigrationStatusCard: React.FC<MigrationStatusCardProps> = ({ migrations }) => {
    const [validating, setValidating] = useState(false);
    const { toast } = useToast();

    const handleValidate = async () => {
        setValidating(true);
        try {
            await databaseOperationsApi.validateMigrations();
            toast({
                title: 'Validation Complete',
                description: 'Database schema and migration history are consistent.',
            });
        } catch {
            toast({
                title: 'Validation Failed',
                description: 'Inconsistencies detected in database schema.',
                variant: 'destructive',
            });
        } finally {
            setValidating(false);
        }
    };

    return (
        <Card className="shadow-sm overflow-hidden">
            <CardHeader className="bg-muted/30 pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <History className="w-4 h-4 text-primary" />
                    Migrations & Schema
                </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
                <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Current Version</span>
                    <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-[10px]">
                        {migrations.current_version || 'unknown'}
                    </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                    <span className="text-muted-foreground">Target Version</span>
                    <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-[10px]">
                        {migrations.latest_version || 'unknown'}
                    </span>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2">
                    <div className="flex flex-col items-center p-2 rounded bg-muted/20 border border-border/40">
                        <span className="text-[10px] uppercase font-bold text-muted-foreground mb-1">Pending</span>
                        <span className={cn(
                            "text-lg font-mono",
                            migrations.pending_count > 0 ? "text-yellow-600" : "text-muted-foreground/40"
                        )}>
                            {migrations.pending_count}
                        </span>
                    </div>
                    <div className="flex flex-col items-center p-2 rounded bg-muted/20 border border-border/40">
                        <span className="text-[10px] uppercase font-bold text-muted-foreground mb-1">Failed</span>
                        <span className={cn(
                            "text-lg font-mono",
                            migrations.failed_count > 0 ? "text-destructive" : "text-muted-foreground/40"
                        )}>
                            {migrations.failed_count}
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-border/40">
                    <div className={cn(
                        "p-1.5 rounded-full",
                        migrations.status === 'healthy' ? "bg-green-500/10 text-green-500" : "bg-yellow-500/10 text-yellow-500"
                    )}>
                        <ShieldCheck className="w-4 h-4" />
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-tighter">Consistency</p>
                        <p className="text-xs truncate">{migrations.validation_status || 'Verified consistent'}</p>
                    </div>
                </div>
            </CardContent>
            <CardFooter className="bg-muted/10 p-3 flex gap-2">
                <Button 
                    size="sm" 
                    variant="secondary" 
                    className="flex-1 h-8 text-[10px] gap-1.5"
                    onClick={handleValidate}
                    disabled={validating}
                >
                    <FileSearch className={cn("w-3 h-3", validating && "animate-pulse")} />
                    Validate Schema
                </Button>
                {migrations.pending_count > 0 && (
                    <Button 
                        size="sm" 
                        variant="default" 
                        className="flex-1 h-8 text-[10px] gap-1.5"
                    >
                        Run Migrations
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
};
