import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ShieldAlert, RefreshCw, Terminal } from 'lucide-react';

interface DatabaseOperationsErrorStateProps {
    error: string;
    onRetry: () => void;
}

export const DatabaseOperationsErrorState: React.FC<DatabaseOperationsErrorStateProps> = ({ error, onRetry }) => {
    return (
        <div className="flex items-center justify-center min-h-[400px]">
            <Card className="max-w-md w-full border-destructive/20 shadow-lg shadow-destructive/5">
                <CardContent className="pt-10 pb-10 flex flex-col items-center text-center space-y-4">
                    <div className="bg-destructive/10 p-4 rounded-full">
                        <ShieldAlert className="w-10 h-10 text-destructive" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-xl font-bold text-destructive">Operational Sync Failure</h3>
                        <p className="text-sm text-muted-foreground">
                            Karen could not reach the admin health service. This may be due to insufficient permissions or a backend network failure.
                        </p>
                    </div>
                    
                    <div className="w-full bg-background border rounded p-3 text-left overflow-auto max-h-32">
                        <div className="flex items-center gap-2 mb-1 text-[10px] text-muted-foreground uppercase font-bold">
                            <Terminal className="w-3 h-3" />
                            Error Trace
                        </div>
                        <code className="text-[10px] font-mono text-destructive break-all">{error}</code>
                    </div>

                    <Button onClick={onRetry} variant="default" className="gap-2 w-full">
                        <RefreshCw className="w-4 h-4" />
                        Reconnect to Health Service
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
};
