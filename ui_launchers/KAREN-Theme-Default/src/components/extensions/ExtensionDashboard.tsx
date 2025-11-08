"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Plug, Settings, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Extension {
  id: string;
  name: string;
  description: string;
  version: string;
  enabled: boolean;
  author?: string;
  category?: string;
}

export interface ExtensionDashboardProps {
  extensions?: Extension[];
  onToggle?: (id: string, enabled: boolean) => void;
  onConfigure?: (id: string) => void;
  onRemove?: (id: string) => void;
  className?: string;
}

export default function ExtensionDashboard({
  extensions = [],
  onToggle,
  onConfigure,
  onRemove,
  className,
}: ExtensionDashboardProps) {
  const [localExtensions, setLocalExtensions] = useState<Extension[]>(extensions);

  const handleToggle = (id: string, enabled: boolean) => {
    setLocalExtensions(prev =>
      prev.map(ext => ext.id === id ? { ...ext, enabled } : ext)
    );
    if (onToggle) {
      onToggle(id, enabled);
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Extensions</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Manage your installed extensions
          </p>
        </div>
        <Badge variant="secondary">
          {localExtensions.filter(e => e.enabled).length} / {localExtensions.length} active
        </Badge>
      </div>

      {localExtensions.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Plug className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-400">No extensions installed</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {localExtensions.map((extension) => (
            <Card key={extension.id} className={cn(
              'relative transition-all',
              !extension.enabled && 'opacity-60'
            )}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{extension.name}</CardTitle>
                    <CardDescription className="text-sm mt-1">
                      v{extension.version}
                    </CardDescription>
                  </div>
                  <Switch
                    checked={extension.enabled}
                    onCheckedChange={(checked) => handleToggle(extension.id, checked)}
                  />
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {extension.description}
                </p>

                <div className="flex flex-wrap gap-2">
                  {extension.category && (
                    <Badge variant="outline">{extension.category}</Badge>
                  )}
                  {extension.author && (
                    <Badge variant="secondary">by {extension.author}</Badge>
                  )}
                </div>
              </CardContent>

              <CardFooter className="gap-2">
                {onConfigure && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onConfigure(extension.id)}
                    className="flex-1"
                  >
                    <Settings className="h-3 w-3 mr-1" />
                    Configure
                  </Button>
                )}
                {onRemove && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemove(extension.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export { ExtensionDashboard };
export type { Extension };
