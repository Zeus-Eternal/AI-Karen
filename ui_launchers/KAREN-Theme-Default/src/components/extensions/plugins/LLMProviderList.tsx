"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plug } from "lucide-react";

interface ProviderInfo {
  id: string;
  name: string;
  status: "healthy" | "error" | "unknown";
  model: string;
}

export default function LLMProviderList() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setProviders([
        { id: "openai", name: "OpenAI", status: "healthy", model: "gpt-3.5-turbo" },
        { id: "anthropic", name: "Anthropic", status: "unknown", model: "claude-3" },
      ]);
    });

    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div className="space-y-4">
      {providers.map((p) => (
        <Card key={p.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm flex items-center gap-1 md:text-base lg:text-lg">
              <Plug className="h-4 w-4 " /> {p.name}
            </CardTitle>
            <Badge variant={p.status === "healthy" ? "default" : "destructive"}>{p.status}</Badge>
          </CardHeader>
          <CardContent className="text-sm md:text-base lg:text-lg">
            Model: <span className="font-mono">{p.model}</span>
          </CardContent>
          <CardFooter>
            <Button size="sm" variant="outline" >Configure</Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
