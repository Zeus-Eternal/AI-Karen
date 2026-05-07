import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Shield, ShieldAlert, ShieldCheck, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { StorageTierHealth } from '@/lib/database-operations-api';

interface DatabaseCircuitBreakerPanelProps {
    tiers: StorageTierHealth[];
}

export const DatabaseCircuitBreakerPanel: React.FC<DatabaseCircuitBreakerPanelProps> = ({ tiers }) => {
    return (
        <Card className="border-border/40 shadow-none bg-muted/10">
            <CardContent className="pt-6 space-y-4">
                <div className="flex items-center gap-3 mb-4">
                    <Shield className="w-5 h-5 text-primary" />
                    <div>
                        <h3 className="text-sm font-semibold">Circuit Breaker Registry</h3>
                        <p className="text-xs text-muted-foreground">Self-healing protection for storage dependencies</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {tiers.map((tier) => {
                        const state = tier.circuit_breaker_state || 'closed';
                        const isTripped = state === 'open' || state === 'half-open';
                        
                        return (
                            <div key={tier.tier} className="flex items-center justify-between p-3 rounded-lg bg-background border shadow-sm group transition-all hover:border-primary/20">
                                <div className="flex items-center gap-3">
                                    <div className={cn(
                                        "p-1.5 rounded-md",
                                        state === 'closed' ? "bg-green-500/10 text-green-600" :
                                        state === 'half-open' ? "bg-yellow-500/10 text-yellow-600" :
                                        "bg-destructive/10 text-destructive"
                                    )}>
                                        {state === 'closed' ? <ShieldCheck className="w-4 h-4" /> :
                                         state === 'half-open' ? <Zap className="w-4 h-4" /> :
                                         <ShieldAlert className="w-4 h-4" />}
                                    </div>
                                    <div>
                                        <p className="text-xs font-bold uppercase tracking-wider">{tier.tier}</p>
                                        <p className="text-[10px] text-muted-foreground font-mono">database.{tier.tier}</p>
                                    </div>
                                </div>
                                <Badge variant={state === 'closed' ? 'outline' : isTripped ? 'destructive' : 'secondary'} className="text-[10px] h-5">
                                    {state.toUpperCase()}
                                </Badge>
                            </div>
                        );
                    })}

                    {/* Extra breakers not tied to tiers */}
                    <div className="flex items-center justify-between p-3 rounded-lg bg-background border shadow-sm">
                        <div className="flex items-center gap-3">
                            <div className="p-1.5 rounded-md bg-green-500/10 text-green-600">
                                <ShieldCheck className="w-4 h-4" />
                            </div>
                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider">Writeback</p>
                                <p className="text-[10px] text-muted-foreground font-mono">memory.writeback</p>
                            </div>
                        </div>
                        <Badge variant="outline" className="text-[10px] h-5 uppercase">CLOSED</Badge>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-background border shadow-sm">
                        <div className="flex items-center gap-3">
                            <div className="p-1.5 rounded-md bg-green-500/10 text-green-600">
                                <ShieldCheck className="w-4 h-4" />
                            </div>
                            <div>
                                <p className="text-xs font-bold uppercase tracking-wider">Projections</p>
                                <p className="text-[10px] text-muted-foreground font-mono">memory.projection</p>
                            </div>
                        </div>
                        <Badge variant="outline" className="text-[10px] h-5 uppercase">CLOSED</Badge>
                    </div>
                </div>
                
                <p className="text-[10px] text-muted-foreground text-center pt-2 italic">
                    Breakers automatically open on repeated failures to prevent system-wide cascading outages.
                </p>
            </CardContent>
        </Card>
    );
};
