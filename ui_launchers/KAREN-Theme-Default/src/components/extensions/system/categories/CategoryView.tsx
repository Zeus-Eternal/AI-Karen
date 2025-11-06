"use client";

import React, { useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Layers } from "lucide-react";

export interface CategoryViewItem {
  id: string;
  name: string;
  displayName?: string;
  category: string;
  status: 'active' | 'inactive' | 'loading' | 'error' | 'disabled';
  description?: string;
}

export interface CategoryViewProps {
  items: CategoryViewItem[];
  onItemClick?: (id: string) => void;
  maxHeight?: string;
}

const categoryLabels: Record<string, string> = {
  security: 'Security & Authentication',
  performance: 'Performance & Optimization',
  monitoring: 'Monitoring & Alerts',
  data: 'Data & Storage',
  integration: 'Integration & API',
  ui: 'UI & Theming',
  automation: 'Automation & Workflows',
  analytics: 'Analytics & Reporting',
  uncategorized: 'Uncategorized',
};

const categoryIcons: Record<string, string> = {
  security: '🔒',
  performance: '⚡',
  monitoring: '📊',
  data: '💾',
  integration: '🔌',
  ui: '🎨',
  automation: '🤖',
  analytics: '📈',
  uncategorized: '📦',
};

const categoryDescriptions: Record<string, string> = {
  security: 'Authentication, authorization, and security-related extensions',
  performance: 'Performance optimization and resource management extensions',
  monitoring: 'System monitoring, health checks, and alerting extensions',
  data: 'Data storage, caching, and database-related extensions',
  integration: 'API integrations and third-party service connectors',
  ui: 'User interface themes, components, and customization extensions',
  automation: 'Workflow automation and scheduled task extensions',
  analytics: 'Analytics, reporting, and data visualization extensions',
  uncategorized: 'Extensions without a specific category',
};

const statusVariants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  active: 'default',
  inactive: 'secondary',
  loading: 'outline',
  error: 'destructive',
  disabled: 'secondary',
};

export default function CategoryView({
  items,
  onItemClick,
  maxHeight = '600px',
}: CategoryViewProps) {
  const groupedByCategory = useMemo(() => {
    const groups: Record<string, CategoryViewItem[]> = {};

    items.forEach((item) => {
      const category = item.category || 'uncategorized';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(item);
    });

    // Sort categories and items
    return Object.keys(groups)
      .sort()
      .map((category) => ({
        category,
        label: categoryLabels[category] || category,
        icon: categoryIcons[category] || '📦',
        description: categoryDescriptions[category] || '',
        items: groups[category].sort((a, b) =>
          (a.displayName || a.name).localeCompare(b.displayName || b.name)
        ),
      }));
  }, [items]);

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Layers className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-muted-foreground">No extensions found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <ScrollArea style={{ maxHeight }}>
      <div className="space-y-6">
        {groupedByCategory.map(({ category, label, icon, description, items: categoryItems }) => (
          <Card key={category}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{icon}</span>
                <div className="flex-1">
                  <CardTitle className="text-lg">{label}</CardTitle>
                  <CardDescription className="text-sm mt-1">
                    {description}
                  </CardDescription>
                </div>
                <Badge variant="secondary">{categoryItems.length}</Badge>
              </div>
            </CardHeader>

            <CardContent>
              <div className="space-y-2">
                {categoryItems.map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors ${
                      onItemClick ? 'cursor-pointer' : ''
                    }`}
                    onClick={() => onItemClick?.(item.id)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">
                          {item.displayName || item.name}
                        </span>
                        <Badge variant={statusVariants[item.status]} className="text-xs">
                          {item.status}
                        </Badge>
                      </div>
                      {item.description && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                          {item.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}

export { CategoryView };
export type { CategoryViewProps, CategoryViewItem };
