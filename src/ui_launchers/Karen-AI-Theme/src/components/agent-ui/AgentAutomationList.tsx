import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Play, Pause, Trash2, Edit3, Calendar, History, Shield, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Automation {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'failed' | 'completed' | 'pending_approval';
  trigger: {
    type: string;
    schedule?: string;
  };
  last_run_at?: string;
  next_run_at?: string;
  risk_level: string;
}

export const AgentAutomationList: React.FC = () => {
  const [automations, setAutomations] = useState<Automation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAutomations = async () => {
      try {
        const response = await fetch('/api/automations/');
        const data = await response.json();
        setAutomations(data);
      } catch (err) {
        console.error('Failed to fetch automations', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAutomations();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'paused': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'failed': return 'bg-destructive/10 text-destructive border-destructive/20';
      case 'pending_approval': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse">Loading Automations...</div>;

  return (
    <div className="space-y-4 p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Agent Automations</h2>
          <p className="text-muted-foreground text-sm">Manage your scheduled tasks and autonomous agents.</p>
        </div>
        <Button>
          <Calendar className="w-4 h-4 mr-2" />
          New Automation
        </Button>
      </div>

      {automations.length === 0 ? (
        <Card className="border-dashed py-12 flex flex-col items-center text-center">
          <div className="bg-muted p-4 rounded-full mb-4">
            <Calendar className="w-8 h-8 text-muted-foreground" />
          </div>
          <CardTitle className="text-lg">No automations found</CardTitle>
          <p className="text-muted-foreground text-sm max-w-xs mt-2">
            Ask Karen to set up a task for you, or create one manually.
          </p>
          <Button variant="outline" className="mt-6">Create your first automation</Button>
        </Card>
      ) : (
        <div className="grid gap-4">
          {automations.map((auto) => (
            <Card key={auto.id} className="group hover:shadow-md transition-all">
              <CardContent className="p-0">
                <div className="flex flex-col md:flex-row md:items-center">
                  <div className={cn("w-1.5 self-stretch rounded-l-lg", 
                    auto.status === 'active' ? "bg-green-500" : "bg-yellow-500"
                  )} />
                  
                  <div className="flex-1 p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-base">{auto.name}</h3>
                          <Badge variant="outline" className={cn("text-[10px] h-4", getStatusColor(auto.status))}>
                            {auto.status.toUpperCase()}
                          </Badge>
                          {auto.risk_level === 'high' && (
                            <Badge variant="destructive" className="text-[10px] h-4">HIGH RISK</Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-1">{auto.description}</p>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button size="icon" variant="ghost" className="h-8 w-8">
                          {auto.status === 'active' ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                        </Button>
                        <Button size="icon" variant="ghost" className="h-8 w-8">
                          <Edit3 className="w-3.5 h-3.5" />
                        </Button>
                        <Button size="icon" variant="ghost" className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10">
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-border/50">
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter">Schedule</p>
                        <p className="text-xs flex items-center gap-1.5 italic">
                          <Calendar className="w-3 h-3" />
                          {auto.trigger.schedule || 'Manual'}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter">Next Run</p>
                        <p className="text-xs">{auto.next_run_at || 'N/A'}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter">Last Result</p>
                        <p className="text-xs flex items-center gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-green-500" />
                          Success
                        </p>
                      </div>
                      <div className="flex items-end justify-end">
                        <Button size="sm" variant="outline" className="h-7 text-[10px]">
                          <History className="w-3 h-3 mr-1.5" />
                          View History
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
