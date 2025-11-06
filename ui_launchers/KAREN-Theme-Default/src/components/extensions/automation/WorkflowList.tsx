"use client";

import React from 'react';
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";

export interface WorkflowStep {
  name: string;
  action: string;
}

export interface WorkflowInfo {
  id: string;
  name: string;
  status: "idle" | "running" | "failed" | "completed";
  steps: WorkflowStep[];
}

export default function WorkflowList() {
  const [workflows, setWorkflows] = useState<WorkflowInfo[]>([]);
  const { toast } = useToast();

  useEffect(() => {
    // Placeholder data; normally fetched from Workflow Builder extension
    setWorkflows([
      {
        id: "wf1",
        name: "Release Pipeline",
        status: "idle",
        steps: [
          { name: "Build", action: "build" },
          { name: "Test", action: "test" },
          { name: "Deploy", action: "deploy" },
        ],
      },
    ]);
  }, []);

  const executeWorkflow = (id: string) => {
    setWorkflows(prev => prev.map(w => w.id === id ? { ...w, status: "running" } : w));
    setTimeout(() => {
      setWorkflows(prev => prev.map(w => w.id === id ? { ...w, status: "completed" } : w));
      toast({ title: "Workflow completed", description: id });
    }, 1000);
  };

  return (
    <div className="space-y-4">
      {workflows.map(wf => (
        <Card key={wf.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm md:text-base lg:text-lg">{wf.name}</CardTitle>
            <Badge variant={wf.status === "failed" ? "destructive" : wf.status === "running" ? "default" : "secondary"}>
              {wf.status}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-2 text-sm md:text-base lg:text-lg">
            {wf.steps.map((step, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span>{step.name}</span>
                <Input className="w-40" value={step.action} readOnly />
              </div>
            ))}
          </CardContent>
          <CardFooter className="flex items-center justify-between gap-2">
            <Textarea className="flex-1" placeholder="Variables (JSON)" />
            <Button size="sm" onClick={() => executeWorkflow(wf.id)}>Execute</Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
