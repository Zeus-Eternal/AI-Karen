import React, { useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { Filter } from 'lucide-react';
import type { CategoryInfo, PluginCategory } from '@/types/plugin';

interface CategoryFilterProps {
  categories: CategoryInfo[];
  selectedCategory?: PluginCategory;
  onCategoryChange: (category: PluginCategory | undefined) => void;
  className?: string;
}

/*
 * Icons are display hints only.
 * Plugin category authority comes from the backend/plugin registry payload,
 * not from this map. Unknown categories still render cleanly.
 */
const CATEGORY_ICON_HINTS: Record<string, string> = {
  productivity: '⚡',
  communication: '💬',
  automation: '🤖',
  analytics: '📊',
  utilities: '🛠️',
  development: '💻',
  integration: '🔗',
  security: '🔒',
  ai_ml: '🧠',
};

const DEFAULT_CATEGORY_ICON = '📦';

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const getCategoryIcon = (categoryName: unknown): string => {
  const normalizedName = cleanString(categoryName).toLowerCase();

  return CATEGORY_ICON_HINTS[normalizedName] || DEFAULT_CATEGORY_ICON;
};

const getCategoryDisplayName = (category: CategoryInfo): string => {
  const displayName = cleanString(category.display_name);
  const name = cleanString(category.name);

  return displayName || name.replace(/_/g, ' ') || 'Uncategorized';
};

const getPluginCount = (category: CategoryInfo): number => {
  const count = Number(category.plugin_count);

  return Number.isFinite(count) && count > 0 ? Math.floor(count) : 0;
};

export function CategoryFilter({
  categories,
  selectedCategory,
  onCategoryChange,
  className = '',
}: CategoryFilterProps) {
  const safeCategories = useMemo(() => {
    return Array.isArray(categories)
      ? categories.filter((category) => cleanString(category?.name))
      : [];
  }, [categories]);

  const selectedCategoryName = cleanString(selectedCategory);

  const handleClear = () => {
    onCategoryChange(undefined);
  };

  return (
    <section className={`flex flex-col gap-3 ${className}`.trim()}>
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <h3 className="text-sm font-medium">Categories</h3>
      </div>

      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Filter plugins by category"
      >
        <button
          type="button"
          onClick={handleClear}
          aria-pressed={!selectedCategoryName}
          className="rounded-full"
        >
          <Badge
            variant={!selectedCategoryName ? 'default' : 'outline'}
            className={`cursor-pointer ${
              !selectedCategoryName ? 'hover:bg-primary/90' : 'hover:bg-accent'
            }`}
          >
            All Categories
          </Badge>
        </button>

        {safeCategories.map((category) => {
          const categoryName = cleanString(category.name) as PluginCategory;
          const isSelected = selectedCategoryName === categoryName;
          const displayName = getCategoryDisplayName(category);
          const pluginCount = getPluginCount(category);

          return (
            <button
              key={categoryName}
              type="button"
              onClick={() => onCategoryChange(categoryName)}
              aria-pressed={isSelected}
              className="rounded-full"
              title={`${displayName} (${pluginCount})`}
            >
              <Badge
                variant={isSelected ? 'default' : 'outline'}
                className={`cursor-pointer hover:bg-accent ${
                  isSelected ? 'hover:bg-primary/90' : ''
                }`}
              >
                <span className="mr-1" aria-hidden="true">
                  {getCategoryIcon(categoryName)}
                </span>
                {displayName}
                <span className="ml-1 opacity-60">({pluginCount})</span>
              </Badge>
            </button>
          );
        })}
      </div>
    </section>
  );
}