"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState, useMemo } from "react";

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description?: string;
}

interface LLMProvider {
  name: string;
  description: string;
}

interface ModelBrowserProps {
  models: ModelInfo[];
  setModels: (models: ModelInfo[]) => void;
  providers: LLMProvider[];
}

/**
 * Lightweight model browser used when the backend is unavailable.
 * Provides basic listing and client-side filtering of models loaded
 * from the parent component.  This prevents React from attempting to
 * render an undefined component which previously caused a crash.
 */
export default function ModelBrowser({ models, setModels, providers }: ModelBrowserProps) {
  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    const lower = filter.toLowerCase();
    return models.filter(m =>
      m.name.toLowerCase().includes(lower) ||
      m.provider.toLowerCase().includes(lower)
    );
  }, [models, filter]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Available Models</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input
          placeholder="Filter by name or provider"
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
        {filtered.length === 0 ? (
          <p className="text-sm text-muted-foreground">No models found.</p>
        ) : (
          <ul className="text-sm space-y-1">
            {filtered.map(model => (
              <li key={model.id} className="flex justify-between">
                <span>{model.name}</span>
                <span className="text-muted-foreground">{model.provider}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
