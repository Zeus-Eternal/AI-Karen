import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, AlertCircle, Power, Zap, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { StorageTierHealth, HealthStatus } from '@/lib/database-operations-api';

interface StorageTierCardsProps {
    tiers: StorageTierHealth[];
}

const statusIcons: Record<HealthStatus, React.ReactNode> = {
    healthy: <CheckCircle2 className="w-4 h-4 text-green-500" />,
    degraded: <AlertCircle className="w-4 h-4 text-yellow-500" />,
    unavailable: <XCircle className="w-4 h-4 text-destructive" />,
    disabled: <Power className="w-4 h-4 text-muted-foreground" />,
    unknown: <Activity className="w-4 h-4 text-muted-foreground" />
};

export const StorageTierCards: React.FC<StorageTierCardsProps> = ({ tiers }) => {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {tiers.map((tier) => (
                <Card key={tier.tier} className={cn(
                    "relative overflow-hidden transition-all hover:shadow-md border-l-4",
                    tier.status === 'healthy' ? "border-l-green-500" :
                    tier.status === 'degraded' ? "border-l-yellow-500" :
                    tier.status === 'unavailable' ? "border-l-destructive" :
                    "border-l-muted"
                )}>
                    <CardHeader className="pb-2 space-y-0">
                        <div className="flex justify-between items-start">
                            <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                                {tier.tier}
                                {statusIcons[tier.status]}
                            </CardTitle>
                            <Badge variant={tier.enabled ? "outline" : "secondary"} className="text-[10px] h-5">
                                {tier.enabled ? 'ENABLED' : 'DISABLED'}
                            </Badge>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-3 pt-0">
                        <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">Connected</span>
                            <span className={cn("font-medium", tier.connected ? "text-green-600" : "text-destructive")}>
                                {tier.connected ? 'YES' : 'NO'}
                            </span>
                        </div>
                        
                        {tier.latency_ms !== null && (
                            <div className="flex justify-between text-xs">
                                <span className="text-muted-foreground">Latency</span>
                                <span className="font-mono flex items-center gap-1">
                                    <Zap className="w-3 h-3 text-yellow-500" />
                                    {tier.latency_ms?.toFixed(1)}ms
                                </span>
                            </div>
                        )}

                        <div className="pt-2 border-t border-border/40 space-y-1">
                            {tier.last_success_at && (
                                <div className="flex justify-between text-[10px]">
                                    <span className="text-muted-foreground">Last Success</span>
                                    <span>{new Date(tier.last_success_at).toLocaleTimeString()}</span>
                                </div>
                            )}
                            {tier.circuit_breaker_state && (
                                <div className="flex justify-between text-[10px]">
                                    <span className="text-muted-foreground">Breaker</span>
                                    <Badge variant="outline" className="text-[8px] h-3 px-1 leading-none">
                                        {tier.circuit_breaker_state.toUpperCase()}
                                    </Badge>
                                </div>
                            )}
                        </div>

                        {tier.error_message && (
                            <p className="text-[10px] text-destructive bg-destructive/5 p-1.5 rounded line-clamp-2 mt-2 border border-destructive/10 italic">
                                {tier.error_message}
                            </p>
                        )}
                    </CardContent>
                </Card>
            ))}
        </div>
    );
};
