"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";

interface SystemExtension {
  id: string;
  name: string;
  category: string;
  enabled: boolean;
  health: "healthy" | "degraded" | "error";
  cpu: number;
  memory: number;
}

export default function SystemExtensionsList() {
  const [exts, setExts] = useState<SystemExtension[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    setExts([
      { id: "analytics", name: "Analytics Dashboard", category: "analytics", enabled: true, health: "healthy", cpu: 10, memory: 200 },
      { id: "comms", name: "Communication Hub", category: "communication", enabled: false, health: "degraded", cpu: 5, memory: 150 },
    ]);
  }, []);

  const toggleExtension = (id: string, en: boolean) => {
    setExts(prev => prev.map(e => e.id === id ? { ...e, enabled: en } : e));
    toast({ title: en ? "Extension enabled" : "Extension disabled", description: id });
  };

  return (
    <div className="space-y-4">
      {exts.map(ext => (
        <Card key={ext.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">{ext.name}</CardTitle>
            <Badge variant={ext.health === "healthy" ? "default" : ext.health === "degraded" ? "secondary" : "destructive"}>
              {ext.health}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-2 text-sm md:text-base lg:text-lg">
            <div className="flex items-center justify-between">
              <span>CPU</span>
              <Progress value={ext.cpu} className="w-40 sm:w-auto md:w-full" />
            </div>
            <div className="flex items-center justify-between">
              <span>Memory</span>
              <Progress value={ext.memory / 500 * 100} className="w-40 sm:w-auto md:w-full" />
            </div>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <Switch checked={ext.enabled} onCheckedChange={(val) => toggleExtension(ext.id, val)} />
            <button size="sm" variant="outline" aria-label="Button">Configure</Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
