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
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Wand2 className="h-4 w-4" /> Copilot Artifacts
          <Badge variant="secondary">{artifacts.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {artifacts.map((artifact) => (
          <div key={artifact.id} className="space-y-2 rounded-md border p-3 bg-muted/40">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-sm">{artifact.title}</div>
                <div className="text-xs text-muted-foreground">
                  {artifact.type} • {artifact.language}
                </div>
              </div>
              <Badge variant="outline" className="text-xs capitalize">
                {artifact.status}
              </Badge>
            </div>
            <div className="text-sm text-muted-foreground whitespace-pre-wrap">
              {artifact.description}
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="default" onClick={() => onApprove(artifact.id)}>
                <Check className="h-4 w-4 mr-1" /> Approve
              </Button>
              <Button size="sm" variant="secondary" onClick={() => onApply(artifact.id)}>
                <Wand2 className="h-4 w-4 mr-1" /> Apply
              </Button>
              <Button size="sm" variant="ghost" onClick={() => onReject(artifact.id)}>
                <X className="h-4 w-4 mr-1" /> Reject
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default CopilotArtifacts;
