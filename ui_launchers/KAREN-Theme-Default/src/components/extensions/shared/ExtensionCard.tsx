"use client";

import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Settings, Trash2, Power, AlertCircle } from "lucide-react";
import { ExtensionStatusBadge } from './ExtensionStatusBadge';
import { ExtensionHealthIndicator } from './ExtensionHealthIndicator';

export interface ExtensionCardProps {
  id: string;
  name: string;
  displayName?: string;
  description: string;
  version: string;
  status: 'active' | 'inactive' | 'loading' | 'error' | 'disabled';
  enabled: boolean;
  health?: 'green' | 'yellow' | 'red' | 'unknown';
  category?: string;
  tags?: string[];
  author?: string;
  onToggle?: (id: string, enabled: boolean) => void;
  onConfigure?: (id: string) => void;
  onRemove?: (id: string) => void;
  errorMessage?: string | null;
  actions?: React.ReactNode;
}

export default function ExtensionCard({
  id,
  name,
  displayName,
  description,
  version,
  status,
  enabled,
  health = 'unknown',
  category,
  tags = [],
  author,
  onToggle,
  onConfigure,
  onRemove,
  errorMessage,
  actions,
}: ExtensionCardProps) {
  return (
    <Card className="relative">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-lg">{displayName || name}</CardTitle>
              <ExtensionStatusBadge status={status} />
              {health !== 'unknown' && (
                <ExtensionHealthIndicator health={health} size="sm" />
              )}
            </div>
            <CardDescription className="text-sm">
              {description}
            </CardDescription>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-2 flex-wrap">
          <Badge variant="outline" className="text-xs">
            v{version}
          </Badge>
          {category && (
            <Badge variant="secondary" className="text-xs capitalize">
              {category}
            </Badge>
          )}
          {author && (
            <Badge variant="outline" className="text-xs">
              {author}
            </Badge>
          )}
        </div>
      </CardHeader>

      {(tags.length > 0 || errorMessage) && (
        <CardContent>
          {tags.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap mb-2">
              {tags.map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          )}

          {errorMessage && (
            <div className="flex items-start gap-2 p-2 bg-destructive/10 border border-destructive/20 rounded-md">
              <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
              <p className="text-xs text-destructive flex-1">{errorMessage}</p>
            </div>
          )}
        </CardContent>
      )}

      <CardFooter className="flex items-center justify-between gap-2 border-t pt-4">
        <div className="flex items-center gap-2">
          {onToggle && (
            <Button
              size="sm"
              variant={enabled ? "default" : "outline"}
              onClick={() => onToggle(id, !enabled)}
              disabled={status === 'loading'}
            >
              <Power className="h-3 w-3 mr-1" />
              {enabled ? 'Disable' : 'Enable'}
            </Button>
          )}

          {onConfigure && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onConfigure(id)}
              disabled={status === 'loading'}
            >
              <Settings className="h-3 w-3 mr-1" />
              Configure
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {actions}

          {onRemove && (
            <Button
              size="sm"
              variant="destructive"
              onClick={() => onRemove(id)}
              disabled={status === 'loading' || enabled}
            >
              <Trash2 className="h-3 w-3 mr-1" />
              Remove
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}

export { ExtensionCard };
export type { ExtensionCardProps };
