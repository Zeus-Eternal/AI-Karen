"use client";

import { useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Video } from "lucide-react";

interface VideoProvider {
  id: string;
  name: string;
  status: "ready" | "unavailable";
}

const DEFAULT_PROVIDERS: readonly VideoProvider[] = [
  { id: "d-id", name: "D-ID", status: "ready" },
  { id: "synthesia", name: "Synthesia", status: "unavailable" },
];

export default function VideoProviderList() {
  const providers = useMemo(
    () => DEFAULT_PROVIDERS.map((provider) => ({ ...provider })),
    []
  );

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
