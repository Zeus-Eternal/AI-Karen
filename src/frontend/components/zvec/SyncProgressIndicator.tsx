/**
 * SyncProgressIndicator Component
 * 
 * Displays real-time sync progress for Zvec-Milvus synchronization.
 * Shows sync status, progress bar, last sync time, and allows manual sync trigger.
 * 
 * @phase 4
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Clock, CheckCircle, AlertCircle, Sync } from 'lucide-react';

interface SyncProgress {
  status: 'idle' | 'syncing' | 'completed' | 'failed';
  progress: number; // 0-100
  synced_count: number;
  total_count: number;
  last_sync_time: string;
  direction: 'zvec_to_milvus' | 'milvus_to_zvec' | 'bidirectional';
  error?: string;
}

interface SyncProgressIndicatorProps {
  userId: string;
  onSyncTrigger?: (direction: 'zvec_to_milvus' | 'milvus_to_zvec' | 'bidirectional') => Promise<void>;
  pollInterval?: number; // milliseconds
  className?: string;
}

export const SyncProgressIndicator: React.FC<SyncProgressIndicatorProps> = ({
  userId,
  onSyncTrigger,
  pollInterval = 5000,
  className = '',
}) => {
  const [syncProgress, setSyncProgress] = useState<SyncProgress>({
    status: 'idle',
    progress: 0,
    synced_count: 0,
    total_count: 0,
    last_sync_time: '',
    direction: 'bidirectional',
  });
  
  const [isSyncing, setIsSyncing] = useState(false);

  /**
   * Fetch current sync status from backend
   */
  const fetchSyncStatus = async () => {
    try {
      const response = await fetch(`/api/zvec/sync/status?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch sync status');
      
      const data = await response.json();
      setSyncProgress(data);
    } catch (error) {
      console.error('Error fetching sync status:', error);
      setSyncProgress(prev => ({
        ...prev,
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    }
  };

  /**
   * Trigger manual sync
   */
  const handleSyncTrigger = async (direction: 'zvec_to_milvus' | 'milvus_to_zvec' | 'bidirectional') => {
    if (isSyncing) return;
    
    setIsSyncing(true);
    try {
      if (onSyncTrigger) {
        await onSyncTrigger(direction);
      } else {
        // Default sync trigger
        const response = await fetch('/api/zvec/sync/trigger', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, direction }),
        });
        
        if (!response.ok) throw new Error('Failed to trigger sync');
      }
      
      // Fetch updated status
      await fetchSyncStatus();
    } catch (error) {
      console.error('Error triggering sync:', error);
      setSyncProgress(prev => ({
        ...prev,
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error',
      }));
    } finally {
      setIsSyncing(false);
    }
  };

  // Poll for sync status updates
  useEffect(() => {
    fetchSyncStatus();
    const interval = setInterval(fetchSyncStatus, pollInterval);
    return () => clearInterval(interval);
  }, [userId, pollInterval]);

  /**
   * Get status badge variant
   */
  const getStatusBadge = () => {
    switch (syncProgress.status) {
      case 'syncing':
        return <Badge variant="secondary" className="animate-pulse">Syncing...</Badge>;
      case 'completed':
        return <Badge variant="default" className="bg-green-500">✓ Synced</Badge>;
      case 'failed':
        return <Badge variant="destructive">✗ Failed</Badge>;
      default:
        return <Badge variant="outline">Idle</Badge>;
    }
  };

  /**
   * Get status icon
   */
  const getStatusIcon = () => {
    switch (syncProgress.status) {
      case 'syncing':
        return <Sync className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  /**
   * Format time ago
   */
  const formatTimeAgo = (timestamp: string) => {
    if (!timestamp) return 'Never';
    
    const now = new Date();
    const syncTime = new Date(timestamp);
    const diffMs = now.getTime() - syncTime.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          Sync Status
        </CardTitle>
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          {getStatusBadge()}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        {(syncProgress.status === 'syncing' || syncProgress.progress > 0) && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Syncing {syncProgress.direction.replace('_', ' → ')}</span>
              <span>{syncProgress.synced_count} / {syncProgress.total_count}</span>
            </div>
            <Progress value={syncProgress.progress} className="h-2" />
            <div className="text-center text-xs font-medium">
              {syncProgress.progress.toFixed(1)}%
            </div>
          </div>
        )}
        
        {/* Error Message */}
        {syncProgress.status === 'failed' && syncProgress.error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{syncProgress.error}</p>
          </div>
        )}
        
        {/* Last Sync Time */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Last sync:</span>
          <span className="font-medium">{formatTimeAgo(syncProgress.last_sync_time)}</span>
        </div>
        
        {/* Sync Stats */}
        {syncProgress.total_count > 0 && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 bg-blue-50 rounded">
              <div className="text-muted-foreground">Vectors synced</div>
              <div className="font-medium text-blue-700">{syncProgress.synced_count.toLocaleString()}</div>
            </div>
            <div className="p-2 bg-green-50 rounded">
              <div className="text-muted-foreground">Success rate</div>
              <div className="font-medium text-green-700">
                {((syncProgress.synced_count / syncProgress.total_count) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        )}
        
        {/* Manual Sync Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSyncTrigger('zvec_to_milvus')}
            disabled={isSyncing}
            className="flex-1"
          >
            <RefreshCw className={`h-3 w-3 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
            Sync → Milvus
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSyncTrigger('milvus_to_zvec')}
            disabled={isSyncing}
            className="flex-1"
          >
            <RefreshCw className={`h-3 w-3 mr-1 ${isSyncing ? 'animate-spin' : ''}`} />
            Sync → Zvec
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Example Usage:
 * 
 * ```tsx
 * <SyncProgressIndicator
 *   userId="user_123"
 *   pollInterval={5000}
 *   onSyncTrigger={async (direction) => {
 *     // Custom sync handling
 *     console.log('Syncing:', direction);
 *   }}
 * />
 * ```
 */
