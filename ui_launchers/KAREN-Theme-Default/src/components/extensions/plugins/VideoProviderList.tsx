"use client";

import React from 'react';
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Video } from "lucide-react";

export interface VideoProvider {
  id: string;
  name: string;
  status: "ready" | "unavailable";
}

export default function VideoProviderList() {
  const [providers, setProviders] = useState<VideoProvider[]>([]);

  useEffect(() => {
    // Placeholder data. Real implementation would check backend for available visual providers
    setProviders([
      { id: "d-id", name: "D-ID", status: "ready" },
      { id: "synthesia", name: "Synthesia", status: "unavailable" },
    ]);
  }, []);

  return (
    <div className="space-y-4">
      {providers.map((p) => (
        <Card key={p.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm flex items-center gap-1 md:text-base lg:text-lg">
              <Video className="h-4 w-4 " /> {p.name}
            </CardTitle>
            <Badge variant={p.status === "ready" ? "default" : "secondary"}>{p.status}</Badge>
          </CardHeader>
          <CardContent className="text-sm md:text-base lg:text-lg">Visual provider</CardContent>
        </Card>
      ))}
    </div>
  );
}
