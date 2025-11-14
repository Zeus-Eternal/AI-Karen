"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Activity, RefreshCw, X } from "lucide-react";
import { getKarenBackend } from "@/lib/karen-backend";
import { useToast } from "@/hooks/use-toast";

type RoutingEvent = {
  timestamp?: string | number;
  correlation_id?: string;
  provider?: string;
  model?: string;
  confidence?: number;
  reason?: string;
  task_type?: string;
  event?: string;
};

interface RoutingHistoryProps {
  onClose?: () => void;
  limit?: number;
}

type RoutingHistoryResponse = {
  status: string;
  output?: {
    events?: RoutingEvent[];
  };
};

export const RoutingHistory: React.FC<RoutingHistoryProps> = ({ onClose, limit = 50 }) => {
  const backend = getKarenBackend();
  const { toast } = useToast();
  const [events, setEvents] = useState<RoutingEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await backend.makeRequestPublic<RoutingHistoryResponse>("/api/copilot/start", {
        method: "POST",
        body: JSON.stringify({ action: "routing.audit", payload: { limit } }),
      });
      const out = res.output ?? {};
      setEvents(out.events ?? []);
    } catch (error) {
      console.error("Failed to load routing history", error);
      toast({ variant: "destructive", title: "Failed to load routing history" });
    } finally {
      setLoading(false);
    }
  }, [backend, limit, toast]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center">
      <Card className="w-[90vw] max-w-3xl max-h-[80vh] overflow-hidden ">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4 " /> Routing History
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">last {limit}</Badge>
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={load} disabled={loading} title="Refresh" className="h-8 w-8 p-0 ">
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose} title="Close" className="h-8 w-8 p-0 ">
              <X className="h-4 w-4 " />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <ScrollArea className="h-[60vh] pr-2">
            <div className="space-y-2">
              {events.length === 0 && (
                <div className="text-sm text-muted-foreground py-6 text-center md:text-base lg:text-lg">No recent routing events</div>
              )}
              {events.map((e, idx) => (
                <div key={`${e.correlation_id || idx}-${idx}`} className="border rounded-md p-2 text-xs sm:text-sm md:text-base">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{e.event || 'routing.done'}</Badge>
                      {e.task_type && <Badge variant="outline">{e.task_type}</Badge>}
                    </div>
                    <div className="text-muted-foreground">
                      {typeof e.confidence === 'number' ? `${Math.round(e.confidence*100)}%` : ''}
                    </div>
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="">Model: <span className="font-medium">{e.provider ? `${e.provider}/` : ''}{e.model || 'unknown'}</span></span>
                    {e.correlation_id && (
                      <span className="text-muted-foreground">corr: {e.correlation_id}</span>
                    )}
                    {e.timestamp && (
                      <span className="text-muted-foreground">{new Date(e.timestamp).toLocaleString()}</span>
                    )}
                  </div>
                  {e.reason && (
                    <div className="mt-1 text-muted-foreground">{e.reason}</div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default RoutingHistory;
