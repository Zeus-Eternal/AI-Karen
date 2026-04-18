import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Filter } from 'lucide-react';
import { PluginCategory, CategoryInfo } from '@/types/plugin';

interface CategoryFilterProps {
  categories: CategoryInfo[];
  selectedCategory?: PluginCategory;
  onCategoryChange: (category: PluginCategory | undefined) => void;
  className?: string;
}

const categoryIcons: Record<string, string> = {
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

export function CategoryFilter({ 
  categories, 
  selectedCategory, 
  onCategoryChange,
  className 
}: CategoryFilterProps) {
  const handleClear = () => {
    onCategoryChange(undefined);
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium">Categories</h3>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {!selectedCategory ? (
          <Badge variant="default" className="cursor-pointer hover:bg-primary/90">
            All Categories
          </Badge>
        ) : (
          <Badge 
            variant="outline" 
            className="cursor-pointer hover:bg-accent"
            onClick={handleClear}
          >
            All Categories
          </Badge>
        )}
        
        {categories.map((category) => (
          <Badge
            key={category.name}
            variant={selectedCategory === category.name ? 'default' : 'outline'}
            className={`cursor-pointer hover:bg-accent ${
              selectedCategory === category.name ? 'hover:bg-primary/90' : ''
            }`}
            onClick={() => onCategoryChange(category.name as PluginCategory)}
          >
            <span className="mr-1">{categoryIcons[category.name] || '📦'}</span>
            {category.display_name}
            <span className="ml-1 opacity-60">({category.plugin_count})</span>
          </Badge>
        ))}
      </div>
    </div>
  );
}
