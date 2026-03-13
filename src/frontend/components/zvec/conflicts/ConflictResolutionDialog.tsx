/**
 * ConflictResolutionDialog Component
 * 
 * Interactive UI for resolving sync conflicts between Zvec and Milvus.
 * Shows conflict details, allows manual resolution, and displays resolution history.
 * 
 * @phase 4
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  GitCompareArrows,
  User,
  Calendar,
  Eye,
  EyeOff,
  History
} from 'lucide-react';

interface Conflict {
  conflict_id: string;
  memory_id: string;
  conflict_type: 'timestamp_conflict' | 'data_conflict' | 'version_conflict';
  local_data: {
    text: string;
    timestamp: string;
    version: number;
    user_id?: string;
  };
  remote_data: {
    text: string;
    timestamp: string;
    version: number;
    user_id?: string;
  };
  auto_resolved?: boolean;
  resolution_strategy?: 'last_write_wins' | 'server_wins' | 'client_wins' | 'merge';
  timestamp: string;
}

interface ResolutionHistory {
  conflict_id: string;
  resolution_strategy: string;
  resolved_at: string;
  resolved_by: 'auto' | 'user';
}

interface ConflictResolutionDialogProps {
  userId: string;
  pollInterval?: number; // milliseconds
  onResolve?: (conflictId: string, strategy: string) => Promise<void>;
  className?: string;
}

export const ConflictResolutionDialog: React.FC<ConflictResolutionDialogProps> = ({
  userId,
  pollInterval = 30000, // Check every 30 seconds
  onResolve,
  className = '',
}) => {
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [resolutionHistory, setResolutionHistory] = useState<ResolutionHistory[]>([]);
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('last_write_wins');
  const [isLoading, setIsLoading] = useState(true);
  const [isResolving, setIsResolving] = useState(false);
  const [open, setOpen] = useState(false);

  /**
   * Fetch conflicts from backend
   */
  const fetchConflicts = async () => {
    try {
      const response = await fetch(`/api/zvec/conflicts/list?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch conflicts');
      
      const data: Conflict[] = await response.json();
      setConflicts(data);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching conflicts:', error);
      setIsLoading(false);
    }
  };

  /**
   * Fetch resolution history
   */
  const fetchResolutionHistory = async () => {
    try {
      const response = await fetch(`/api/zvec/conflicts/history?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch resolution history');
      
      const data: ResolutionHistory[] = await response.json();
      setResolutionHistory(data);
    } catch (error) {
      console.error('Error fetching resolution history:', error);
    }
  };

  /**
   * Resolve a conflict
   */
  const handleResolve = async () => {
    if (!selectedConflict || isResolving) return;
    
    setIsResolving(true);
    try {
      if (onResolve) {
        await onResolve(selectedConflict.conflict_id, selectedStrategy);
      } else {
        // Default resolve API
        const response = await fetch('/api/zvec/conflicts/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            conflict_id: selectedConflict.conflict_id,
            resolution_strategy: selectedStrategy,
          }),
        });
        
        if (!response.ok) throw new Error('Failed to resolve conflict');
      }
      
      // Refresh conflicts and history
      await fetchConflicts();
      await fetchResolutionHistory();
      
      // Clear selection and close dialog
      setSelectedConflict(null);
      setOpen(false);
    } catch (error) {
      console.error('Error resolving conflict:', error);
    } finally {
      setIsResolving(false);
    }
  };

  /**
   * Auto-resolve all conflicts
   */
  const handleAutoResolve = async () => {
    if (conflicts.length === 0) return;
    
    setIsResolving(true);
    try {
      const response = await fetch('/api/zvec/conflicts/auto-resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      
      if (!response.ok) throw new Error('Failed to auto-resolve conflicts');
      
      // Refresh conflicts and history
      await fetchConflicts();
      await fetchResolutionHistory();
    } catch (error) {
      console.error('Error auto-resolving conflicts:', error);
    } finally {
      setIsResolving(false);
    }
  };

  /**
   * Format timestamp to human readable
   */
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  /**
   * Get conflict type badge
   */
  const getConflictTypeBadge = (type: string) => {
    switch (type) {
      case 'timestamp_conflict':
        return <Badge variant="outline">Timestamp Conflict</Badge>;
      case 'data_conflict':
        return <Badge variant="destructive">Data Conflict</Badge>;
      case 'version_conflict':
        return <Badge variant="secondary">Version Conflict</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  /**
   * Compare timestamps
   */
  const compareTimestamps = (local: string, remote: string) => {
    const localDate = new Date(local);
    const remoteDate = new Date(remote);
    if (localDate > remoteDate) return 'local';
    if (remoteDate > localDate) return 'remote';
    return 'equal';
  };

  // Poll for conflicts
  useEffect(() => {
    fetchConflicts();
    fetchResolutionHistory();
    const interval = setInterval(fetchConflicts, pollInterval);
    return () => clearInterval(interval);
  }, [userId, pollInterval]);

  // Count unresolved conflicts
  const unresolvedCount = conflicts.filter(c => !c.auto_resolved).length;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className={className}>
          <AlertTriangle className={`h-4 w-4 mr-2 ${unresolvedCount > 0 ? 'animate-pulse' : ''}`} />
          Conflicts {unresolvedCount > 0 && `(${unresolvedCount})`}
        </Button>
      </DialogTrigger>

      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              Sync Conflicts
            </div>
            <Badge variant={unresolvedCount > 0 ? 'destructive' : 'default'}>
              {unresolvedCount} Unresolved
            </Badge>
          </DialogTitle>
          <DialogDescription>
            {unresolvedCount > 0 
              ? 'You have sync conflicts that need manual resolution. Review the conflicts below and choose how to resolve them.'
              : 'No sync conflicts detected. All changes have been synced successfully.'
            }
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4">
          {/* Auto-Resolve Button */}
          {unresolvedCount > 0 && (
            <div className="flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={handleAutoResolve}
                disabled={isResolving}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Auto-Resolve All
              </Button>
            </div>
          )}

          {/* Conflicts List */}
          <ScrollArea className="h-[400px] pr-4">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Clock className="h-6 w-6 animate-pulse text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading conflicts...</span>
              </div>
            ) : conflicts.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                <p>No conflicts found</p>
              </div>
            ) : (
              <div className="space-y-3">
                {conflicts.map((conflict) => (
                  <Card
                    key={conflict.conflict_id}
                    className={`cursor-pointer transition-colors ${
                      selectedConflict?.conflict_id === conflict.conflict_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'hover:border-blue-300'
                    }`}
                    onClick={() => setSelectedConflict(conflict)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-sm font-semibold">
                              {conflict.local_data.text.substring(0, 50)}...
                            </CardTitle>
                            {getConflictTypeBadge(conflict.conflict_type)}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Calendar className="h-3 w-3" />
                            {formatTimestamp(conflict.timestamp)}
                          </div>
                        </div>
                        {conflict.auto_resolved && (
                          <Badge variant="outline" className="text-xs">
                            Auto-Resolved
                          </Badge>
                        )}
                      </div>
                    </CardHeader>

                    {selectedConflict?.conflict_id === conflict.conflict_id && (
                      <CardContent className="space-y-4">
                        {/* Local vs Remote Comparison */}
                        <div className="grid grid-cols-2 gap-4">
                          {/* Local Data */}
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Label className="text-sm font-semibold">Local (Zvec)</Label>
                              <Badge variant="outline" className="text-xs">
                                v{conflict.local_data.version}
                              </Badge>
                            </div>
                            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                              <p className="text-sm">{conflict.local_data.text}</p>
                              <div className="mt-2 text-xs text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {formatTimestamp(conflict.local_data.timestamp)}
                                </div>
                                {conflict.local_data.user_id && (
                                  <div className="flex items-center gap-1 mt-1">
                                    <User className="h-3 w-3" />
                                    {conflict.local_data.user_id}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          {/* Remote Data */}
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Label className="text-sm font-semibold">Remote (Milvus)</Label>
                              <Badge variant="outline" className="text-xs">
                                v{conflict.remote_data.version}
                              </Badge>
                            </div>
                            <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                              <p className="text-sm">{conflict.remote_data.text}</p>
                              <div className="mt-2 text-xs text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {formatTimestamp(conflict.remote_data.timestamp)}
                                </div>
                                {conflict.remote_data.user_id && (
                                  <div className="flex items-center gap-1 mt-1">
                                    <User className="h-3 w-3" />
                                    {conflict.remote_data.user_id}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Resolution Strategy Selection */}
                        <div className="space-y-2">
                          <Label className="text-sm font-semibold">Resolution Strategy:</Label>
                          <RadioGroup value={selectedStrategy} onValueChange={setSelectedStrategy}>
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="last_write_wins" id="last_write" />
                                <Label htmlFor="last_write" className="text-sm cursor-pointer">
                                  Last Write Wins - Most recent change
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="server_wins" id="server_wins" />
                                <Label htmlFor="server_wins" className="text-sm cursor-pointer">
                                  Server Wins - Keep remote (Milvus) version
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="client_wins" id="client_wins" />
                                <Label htmlFor="client_wins" className="text-sm cursor-pointer">
                                  Client Wins - Keep local (Zvec) version
                                </Label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <RadioGroupItem value="merge" id="merge" />
                                <Label htmlFor="merge" className="text-sm cursor-pointer">
                                  Merge - Combine both versions (if compatible)
                                </Label>
                              </div>
                            </div>
                          </RadioGroup>
                        </div>

                        {/* Timestamp Comparison Hint */}
                        {conflict.conflict_type === 'timestamp_conflict' && (
                          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                            <div className="flex items-start gap-2 text-sm">
                              <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
                              <div>
                                <p className="font-semibold text-yellow-900">Timestamp Conflict Detected</p>
                                <p className="text-yellow-800">
                                  {compareTimestamps(
                                    conflict.local_data.timestamp,
                                    conflict.remote_data.timestamp
                                  ) === 'local'
                                    ? 'Local version is more recent'
                                    : 'Remote version is more recent'}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Resolution History */}
          {resolutionHistory.length > 0 && (
            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-2">
                <History className="h-4 w-4" />
                <Label className="text-sm font-semibold">Resolution History</Label>
              </div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {resolutionHistory.slice(0, 5).map((history, idx) => (
                  <div key={idx} className="text-xs text-muted-foreground">
                    <span className="font-medium">
                      {history.resolution_strategy}
                    </span>
                    {' - '}
                    <span>{formatTimestamp(history.resolved_at)}</span>
                    {' - '}
                    <span>
                      by {history.resolved_by === 'auto' ? 'System' : 'You'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Close
          </Button>
          {selectedConflict && !selectedConflict.auto_resolved && (
            <Button onClick={handleResolve} disabled={isResolving}>
              <CheckCircle className="h-4 w-4 mr-2" />
              {isResolving ? 'Resolving...' : 'Resolve'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

/**
 * Example Usage:
 * 
 * ```tsx
 * <ConflictResolutionDialog
 *   userId="user_123"
 *   pollInterval={30000}
 *   onResolve={async (conflictId, strategy) => {
 *     console.log('Resolving conflict:', conflictId, 'with strategy:', strategy);
 *   }}
 * />
 * ```
 */
