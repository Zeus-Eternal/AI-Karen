import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SystemCategory } from './types';
import { Settings, Package, Clock } from 'lucide-react';

interface SystemCategoryCardProps {
  category: SystemCategory;
  onToggle?: (categoryId: string) => void;
  onEdit?: (categoryId: string) => void;
  className?: string;
}

export default function SystemCategoryCard({
  category,
  onToggle,
  onEdit,
  className = ''
}: SystemCategoryCardProps) {
  return (
    <Card className={`transition-all duration-200 hover:shadow-md ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Settings className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">{category.name}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {category.description}
              </p>
            </div>
          </div>
          <Badge variant={category.isActive ? 'default' : 'secondary'}>
            {category.isActive ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
            <div className="flex items-center space-x-1">
              <Package className="h-4 w-4" />
              <span>{category.extensionCount} extensions</span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{category.lastUpdated.toLocaleDateString()}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {onToggle && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onToggle(category.id)}
              >
                {category.isActive ? 'Disable' : 'Enable'}
              </Button>
            )}
            {onEdit && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(category.id)}
              >
                Edit
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}