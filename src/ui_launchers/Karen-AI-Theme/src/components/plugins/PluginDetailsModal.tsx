import React from 'react';
import Image from 'next/image';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { PluginStatusBadge } from './PluginStatusBadge';
import {
  Download,
  ExternalLink,
  GitBranch,
  User,
  Star,
  Package,
  CheckCircle2,
  XCircle,
  Calendar,
  Shield,
  Link as LinkIcon,
} from 'lucide-react';
import { PluginDetails } from '@/types/plugin';
import { cn } from '@/lib/utils';

interface PluginDetailsModalProps {
  details: PluginDetails | null;
  loading?: boolean;
  installing?: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInstall?: () => void;
}

export function PluginDetailsModal({
  details,
  loading = false,
  installing = false,
  open,
  onOpenChange,
  onInstall,
}: PluginDetailsModalProps) {
  const plugin = details?.plugin;
  const analytics = details?.analytics;
  const installed = details?.installed;
  const updateAvailable = details?.update_available;

  if (!plugin) {
    return null;
  }

  const compatibilityInfo = plugin.compatibility;
  const isCompatible = !compatibilityInfo || (
    !compatibilityInfo.min_karen_version &&
    !compatibilityInfo.max_karen_version
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start gap-4">
            {plugin.icon && (
              <Image
                src={plugin.icon}
                alt={`${plugin.display_name} icon`}
                width={64}
                height={64}
                className="h-16 w-16 rounded-lg object-cover"
              />

            )}
            <div className="flex-1 min-w-0">
              <DialogTitle className="text-xl">{plugin.display_name}</DialogTitle>
              <DialogDescription className="mt-1">
                {plugin.description}
              </DialogDescription>
              <div className="flex items-center gap-2 mt-2">
                <PluginStatusBadge status={plugin.status} />
                {updateAvailable && (
                  <Badge variant="secondary" className="text-xs">
                    Update Available
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>{plugin.author}</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <GitBranch className="h-4 w-4" />
              <span>v{plugin.version}</span>
            </div>
            {plugin.license && (
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Shield className="h-4 w-4" />
                <span>{plugin.license}</span>
              </div>
            )}
            {plugin.installed_at && (
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>Installed {new Date(plugin.installed_at).toLocaleDateString()}</span>
              </div>
            )}
          </div>

          {analytics && (
            <div className="flex flex-wrap gap-4">
              {plugin.rating !== undefined && (
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  <span className="font-semibold">{plugin.rating.toFixed(1)}</span>
                  <span className="text-sm text-muted-foreground">
                    ({plugin.rating_count} reviews)
                  </span>
                </div>
              )}
              {plugin.downloads !== undefined && (
                <div className="flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  <span className="font-semibold">{plugin.downloads.toLocaleString()}</span>
                  <span className="text-sm text-muted-foreground">downloads</span>
                </div>
              )}
            </div>
          )}

          {compatibilityInfo && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Compatibility</h4>
              <div className={cn(
                "flex items-start gap-2 p-3 rounded-md",
                isCompatible
                  ? "bg-green-500/10 text-green-600 dark:text-green-400"
                  : "bg-red-500/10 text-red-600 dark:text-red-400"
              )}>
                {isCompatible ? (
                  <CheckCircle2 className="h-5 w-5 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="h-5 w-5 shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  {isCompatible ? (
                    <p className="text-sm">This plugin is compatible with your Karen AI version.</p>
                  ) : (
                    <p className="text-sm">
                      This plugin may not be compatible with your Karen AI version.
                      {compatibilityInfo.min_karen_version && (
                        <span> Requires version {compatibilityInfo.min_karen_version} or higher.</span>
                      )}
                      {compatibilityInfo.max_karen_version && (
                        <span> Requires version {compatibilityInfo.max_karen_version} or lower.</span>
                      )}
                    </p>
                  )}
                  {compatibilityInfo.requirements && compatibilityInfo.requirements.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium mb-1">Requirements:</p>
                      <ul className="list-disc list-inside text-xs space-y-1">
                        {compatibilityInfo.requirements.map((req, index) => (
                          <li key={index}>{req}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {plugin.dependencies && plugin.dependencies.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Dependencies</h4>
              <div className="flex flex-wrap gap-2">
                {plugin.dependencies.map((dep, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {plugin.tags && plugin.tags.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {plugin.tags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <Separator />

          <div className="flex flex-wrap gap-2">
            {plugin.homepage_url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(plugin.homepage_url, '_blank')}
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Homepage
              </Button>
            )}
            {plugin.repository_url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(plugin.repository_url, '_blank')}
              >
                <GitBranch className="h-4 w-4 mr-2" />
                Repository
              </Button>
            )}
            {plugin.marketplace_url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(plugin.marketplace_url, '_blank')}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Marketplace
              </Button>
            )}
          </div>
        </div>

        <DialogFooter>
          {installed ? (
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          ) : (
            <Button
              onClick={onInstall}
              disabled={installing || loading || !isCompatible}
              className="flex-1"
            >
              {installing ? (
                <>
                  <span className="animate-spin mr-2">⏳</span>
                  Installing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Install Plugin
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
