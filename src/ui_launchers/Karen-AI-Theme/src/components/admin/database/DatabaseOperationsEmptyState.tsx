import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, RefreshCw } from 'lucide-react';

interface DatabaseOperationsEmptyStateProps {
    onRetry: () => void;
}

export const DatabaseOperationsEmptyState: React.FC<DatabaseOperationsEmptyStateProps> = ({ onRetry }) => {
    return (
        <div className="flex items-center justify-center min-h-[400px]">
            <Card className="max-w-md w-full border-dashed">
                <CardContent className="pt-10 pb-10 flex flex-col items-center text-center space-y-4">
                    <div className="bg-muted p-4 rounded-full">
                        <Database className="w-10 h-10 text-muted-foreground" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-xl font-bold">No Operational Data</h3>
                        <p className="text-sm text-muted-foreground">
                            Karen could not find any active storage tiers or memory projections. 
                            Ensure the backend database services are initialized.
                        </p>
                    </div>
                    <Button onClick={onRetry} variant="outline" className="gap-2">
                        <RefreshCw className="w-4 h-4" />
                        Scan Services
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
};
