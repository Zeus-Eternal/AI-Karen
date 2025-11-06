"use client";

import React from 'react';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Filter } from "lucide-react";

export interface CategoryFilterProps {
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  categoryCounts?: Record<string, number>;
}

const categoryLabels: Record<string, string> = {
  all: 'All Categories',
  security: 'Security & Auth',
  performance: 'Performance',
  monitoring: 'Monitoring',
  data: 'Data & Storage',
  integration: 'Integration & API',
  ui: 'UI & Theming',
  automation: 'Automation',
  analytics: 'Analytics',
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

export default function CategoryFilter({
  categories,
  selectedCategory,
  onCategoryChange,
  categoryCounts = {},
}: CategoryFilterProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Category:</span>
      </div>

      <Select value={selectedCategory} onValueChange={onCategoryChange}>
        <SelectTrigger className="w-64">
          <SelectValue placeholder="Select category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">
            <div className="flex items-center justify-between gap-3 w-full">
              <span>{categoryLabels.all}</span>
              {categoryCounts.all !== undefined && (
                <Badge variant="secondary" className="ml-auto">
                  {categoryCounts.all}
                </Badge>
              )}
            </div>
          </SelectItem>

          {categories
            .filter((cat) => cat !== 'all')
            .map((category) => (
              <SelectItem key={category} value={category}>
                <div className="flex items-center justify-between gap-3 w-full">
                  <span className="flex items-center gap-2">
                    {categoryIcons[category] && (
                      <span>{categoryIcons[category]}</span>
                    )}
                    {categoryLabels[category] || category}
                  </span>
                  {categoryCounts[category] !== undefined && (
                    <Badge variant="secondary" className="ml-auto">
                      {categoryCounts[category]}
                    </Badge>
                  )}
                </div>
              </SelectItem>
            ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export { CategoryFilter };
export type { CategoryFilterProps };
