"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";

interface AgentInfo {
  id: string;
  name: string;
  status: "running" | "stopped" | "error";
  trigger: string;
  action: string;
}

export default function AgentList() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    // Placeholder data - normally fetched from backend extension API
    setAgents([
      { id: "build-agent", name: "Build Agent", status: "running", trigger: "on commit", action: "build" },
      { id: "review-agent", name: "Review Agent", status: "stopped", trigger: "manual", action: "review" },
    ]);
  }, []);

  const toggleAgent = (id: string, enabled: boolean) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, status: enabled ? "running" : "stopped" } : a));
    toast({
      title: enabled ? "Agent started" : "Agent stopped",
      description: `${id} ${enabled ? "is running" : "has stopped"}`,
    });
  };

  return (
    <div className="space-y-4">
      {agents.map(agent => (
        <Card key={agent.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">{agent.name}</CardTitle>
            <Badge variant={agent.status === "running" ? "default" : agent.status === "stopped" ? "secondary" : "destructive"}>
              {agent.status}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-2 text-sm md:text-base lg:text-lg">
            <div className="flex items-center justify-between">
              <span>Trigger</span>
              <input className="w-40 sm:w-auto md:w-full" value={agent.trigger} readOnly />
            </div>
            <div className="flex items-center justify-between">
              <span>Action</span>
              <input className="w-40 sm:w-auto md:w-full" value={agent.action} readOnly />
            </div>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <Switch checked={agent.status === "running"} onCheckedChange={(val) => toggleAgent(agent.id, val)} />
            <button size="sm" variant="outline" aria-label="Button">Configure</Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
