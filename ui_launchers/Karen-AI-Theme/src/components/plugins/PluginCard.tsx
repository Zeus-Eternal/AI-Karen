import React from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PluginStatusBadge } from './PluginStatusBadge';
import { Download, ExternalLink, GitBranch, Star, Package, User, Hash } from 'lucide-react';
import { Plugin } from '@/types/plugin';

interface PluginCardProps {
  plugin: Plugin;
  onInstall?: (pluginId: string, version?: string) => void;
  onDetails?: (pluginId: string) => void;
  onDiscover?: (pluginId: string) => void;
  loading?: boolean;
  className?: string;
}

export function PluginCard({ 
  plugin, 
  onInstall, 
  onDetails, 
  onDiscover, 
  loading = false,
  className 
}: PluginCardProps) {
  const handleInstall = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onInstall) {
      onInstall(plugin.id, plugin.version);
    }
  };

  const handleDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDetails) {
      onDetails(plugin.id);
    }
  };

  const handleDiscover = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDiscover) {
      onDiscover(plugin.id);
    }
  };

  return (
    <Card 
      className={`group hover:shadow-lg transition-all duration-200 cursor-pointer ${className}`}
      onClick={handleDetails}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {plugin.icon && (
                <img 
                  src={plugin.icon} 
                  alt={`${plugin.display_name} icon`} 
                  className="h-8 w-8 rounded-md object-cover"
                />
              )}
              <CardTitle className="text-lg font-semibold truncate">
                {plugin.display_name}
              </CardTitle>
            </div>
            <CardDescription className="text-xs line-clamp-2">
              {plugin.description}
            </CardDescription>
          </div>
          <PluginStatusBadge status={plugin.status} />
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pb-3">
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <User className="h-3 w-3" />
            <span className="truncate max-w-32">{plugin.author}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <GitBranch className="h-3 w-3" />
            <span>v{plugin.version}</span>
          </div>
          {plugin.category && (
            <Badge variant="secondary" className="text-xs">
              {plugin.category}
            </Badge>
          )}
        </div>

        {plugin.tags && plugin.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {plugin.tags.slice(0, 3).map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs py-0">
                <Hash className="h-2 w-2 mr-1" />
                {tag}
              </Badge>
            ))}
            {plugin.tags.length > 3 && (
              <Badge variant="outline" className="text-xs py-0">
                +{plugin.tags.length - 3}
              </Badge>
            )}
          </div>
        )}

        {(plugin.rating || plugin.downloads !== undefined) && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {plugin.rating !== undefined && plugin.rating_count !== undefined && (
              <div className="flex items-center gap-1">
                <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                <span>{plugin.rating.toFixed(1)}</span>
                <span className="opacity-60">({plugin.rating_count})</span>
              </div>
            )}
            {plugin.downloads !== undefined && (
              <div className="flex items-center gap-1">
                <Package className="h-3 w-3" />
                <span>{plugin.downloads.toLocaleString()}</span>
              </div>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2 pt-3 border-t">
        {plugin.status === 'available' ? (
          <>
            <Button 
              size="sm" 
              className="flex-1"
              onClick={handleInstall}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Installing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-1" />
                  Install
                </>
              )}
            </Button>
            {onDiscover && (
              <Button size="sm" variant="outline" onClick={handleDiscover}>
                Discover
              </Button>
            )}
          </>
        ) : plugin.status === 'installed' ? (
          <Button size="sm" variant="outline" className="w-full" onClick={handleDetails}>
            Manage
          </Button>
        ) : (
          <Button size="sm" variant="ghost" className="w-full" onClick={handleDetails}>
            View Details
          </Button>
        )}
        {plugin.marketplace_url && (
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={(e) => {
              e.stopPropagation();
              window.open(plugin.marketplace_url, '_blank');
            }}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
