"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, X, Wand2 } from "lucide-react";
import type { CopilotArtifact } from "../types";

interface CopilotArtifactsProps {
  artifacts: CopilotArtifact[];
  onApprove: (artifactId: string) => void;
  onReject: (artifactId: string) => void;
  onApply: (artifactId: string) => void;
}

const CopilotArtifacts: React.FC<CopilotArtifactsProps> = ({
  artifacts,
  onApprove,
  onReject,
  onApply,
}) => {
  if (artifacts.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2 md:text-base lg:text-lg">
          <Wand2 className="h-4 w-4 sm:w-auto md:w-full" /> Copilot Artifacts
          <Badge variant="secondary">{artifacts.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {artifacts.map((artifact) => (
          <div key={artifact.id} className="space-y-2 rounded-md border p-3 bg-muted/40 sm:p-4 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-sm md:text-base lg:text-lg">{artifact.title}</div>
                <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {artifact.type} • {artifact.language}
                </div>
              </div>
              <Badge variant="outline" className="text-xs capitalize sm:text-sm md:text-base">
                {artifact.status}
              </Badge>
            </div>
            <div className="text-sm text-muted-foreground whitespace-pre-wrap md:text-base lg:text-lg">
              {artifact.description}
            </div>
            <div className="flex gap-2">
              <button size="sm" variant="default" onClick={() = aria-label="Button"> onApprove(artifact.id)}>
                <Check className="h-4 w-4 mr-1 sm:w-auto md:w-full" /> Approve
              </Button>
              <button size="sm" variant="secondary" onClick={() = aria-label="Button"> onApply(artifact.id)}>
                <Wand2 className="h-4 w-4 mr-1 sm:w-auto md:w-full" /> Apply
              </Button>
              <button size="sm" variant="ghost" onClick={() = aria-label="Button"> onReject(artifact.id)}>
                <X className="h-4 w-4 mr-1 sm:w-auto md:w-full" /> Reject
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default CopilotArtifacts;
