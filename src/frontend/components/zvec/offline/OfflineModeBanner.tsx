/**
 * OfflineModeBanner Component
 * 
 * Displays offline mode status with toast/banner notifications.
 * Shows when offline, when sync queue is pending, and when connection is restored.
 * Provides user feedback for offline/online transitions.
 * 
 * @phase 4
 */

import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Wifi, 
  WifiOf, 
  RefreshCw, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  X
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface OfflineStatus {
  is_offline: boolean;
  last_check: string;
  capabilities: {
    local_rag: boolean;
    local_storage: boolean;
    online_sync: boolean;
  };
  queue_size?: number;
  sync_available?: boolean;
}

interface OfflineModeBannerProps {
  userId: string;
  pollInterval?: number; // milliseconds
  onSyncNow?: () => Promise<void>;
  onDismiss?: () => void;
  className?: string;
}

export const OfflineModeBanner: React.FC<OfflineModeBannerProps> = ({
  userId,
  pollInterval = 10000, // Check every 10 seconds
  onSyncNow,
  onDismiss,
  className = '',
}) => {
  const [offlineStatus, setOfflineStatus] = useState<OfflineStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const { toast } = useToast();

  /**
   * Fetch offline status from backend
   */
  const fetchOfflineStatus = async () => {
    try {
      const response = await fetch(`/api/zvec/offline/status?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch offline status');
      
      const data: OfflineStatus = await response.json();
      setOfflineStatus(data);
      
      // Show toast on offline/online transition
      if (data.is_offline && !dismissed) {
        toast({
          title: 'Offline Mode Activated',
          description: 'You can continue using AI-Karen with local features. Your changes will sync when connection is restored.',
          variant: 'warning',
          duration: 5000,
        });
      } else if (!data.is_offline && data.queue_size && data.queue_size > 0) {
        toast({
          title: 'Connection Restored',
          description: `${data.queue_size} items ready to sync. Click to sync now.`,
          variant: 'default',
          action: (
            <Button 
              size="sm" 
              variant="outline" 
              onClick={handleSyncNow}
              className="ml-2"
            >
              Sync Now
            </Button>
          ),
          duration: 10000,
        });
      }
    } catch (error) {
      console.error('Error fetching offline status:', error);
    }
  };

  /**
   * Handle sync now button
   */
  const handleSyncNow = async () => {
    if (isSyncing || !offlineStatus?.sync_available) return;
    
    setIsSyncing(true);
    try {
      if (onSyncNow) {
        await onSyncNow();
      } else {
        // Default sync trigger
        const response = await fetch('/api/zvec/sync/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, direction: 'bidirectional' }),
        });
        
        if (!response.ok) throw new Error('Failed to sync');
      }
      
      toast({
        title: 'Sync Complete',
        description: 'All offline changes have been synced successfully.',
        variant: 'default',
        duration: 3000,
      });
      
      // Refresh status
      await fetchOfflineStatus();
    } catch (error) {
      console.error('Error syncing:', error);
      toast({
        title: 'Sync Failed',
        description: 'Could not sync offline changes. Will retry automatically.',
        variant: 'destructive',
        duration: 5000,
      });
    } finally {
      setIsSyncing(false);
    }
  };

  /**
   * Handle dismiss
   */
  const handleDismiss = () => {
    setDismissed(true);
    if (onDismiss) onDismiss();
  };

  // Poll for offline status
  useEffect(() => {
    fetchOfflineStatus();
    const interval = setInterval(fetchOfflineStatus, pollInterval);
    return () => clearInterval(interval);
  }, [userId, pollInterval]);

  // Don't show if online with no queue or dismissed
  if (!offlineStatus) return null;
  if (!offlineStatus.is_offline && (!offlineStatus.queue_size || offlineStatus.queue_size === 0)) return null;
  if (dismissed && !offlineStatus.is_offline) return null;

  const isOffline = offlineStatus.is_offline;
  const hasQueue = offlineStatus.queue_size && offlineStatus.queue_size > 0;

  return (
    <Alert className={`${className} ${isOffline ? 'bg-yellow-50 border-yellow-200' : 'bg-blue-50 border-blue-200'}`}>
      <div className="flex items-start gap-3 w-full">
        {/* Icon */}
        <div className={`${isOffline ? 'text-yellow-600' : 'text-blue-600'}`}>
          {isOffline ? (
            <WifiOf className="h-5 w-5 animate-pulse" />
          ) : (
            <Wifi className="h-5 w-5" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-2">
          {/* Title */}
          <AlertTitle className={`text-sm font-semibold ${isOffline ? 'text-yellow-900' : 'text-blue-900'}`}>
            {isOffline ? 'You are offline' : 'Back online'}
          </AlertTitle>

          {/* Description */}
          <AlertDescription className={`text-sm ${isOffline ? 'text-yellow-800' : 'text-blue-800'}`}>
            {isOffline ? (
              <div className="space-y-2">
                <p>
                  You can continue using AI-Karen with local features. 
                  Your changes will sync automatically when connection is restored.
                </p>
                
                {/* Capabilities */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {offlineStatus.capabilities.local_rag && (
                    <Badge variant="outline" className="bg-white text-yellow-900 border-yellow-300">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Local Search
                    </Badge>
                  )}
                  {offlineStatus.capabilities.local_storage && (
                    <Badge variant="outline" className="bg-white text-yellow-900 border-yellow-300">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Local Storage
                    </Badge>
                  )}
                  {!offlineStatus.capabilities.online_sync && (
                    <Badge variant="outline" className="bg-yellow-100 text-yellow-900 border-yellow-300">
                      <Clock className="h-3 w-3 mr-1" />
                      Sync Paused
                    </Badge>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {hasQueue ? (
                  <>
                    <p>
                      Your connection has been restored! You have <strong>{offlineStatus.queue_size} items</strong> ready to sync.
                    </p>
                    
                    {/* Sync Button */}
                    <Button
                      size="sm"
                      onClick={handleSyncNow}
                      disabled={isSyncing}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <RefreshCw className={`h-4 w-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
                      {isSyncing ? 'Syncing...' : 'Sync Now'}
                    </Button>
                  </>
                ) : (
                  <p>All changes have been synced successfully.</p>
                )}
              </div>
            )}
          </AlertDescription>

          {/* Queue Progress (if syncing) */}
          {isSyncing && (
            <div className="space-y-1 mt-2">
              <Progress value={50} className="h-2" />
              <p className="text-xs text-muted-foreground">Syncing your changes...</p>
            </div>
          )}
        </div>

        {/* Dismiss Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDismiss}
          className="h-6 w-6 p-0"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </Alert>
  );
};

/**
 * Example Usage:
 * 
 * ```tsx
 * <OfflineModeBanner
 *   userId="user_123"
 *   pollInterval={10000}
 *   onSyncNow={async () => {
 *     // Custom sync handling
 *     console.log('Syncing...');
 *   }}
 *   onDismiss={() => console.log('Banner dismissed')}
 * />
 * ```
 */
