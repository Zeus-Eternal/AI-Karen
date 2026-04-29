export const getStreamingStatus = (
  isBackendOffline: boolean,
  isLoading: boolean,
  processingStatus: string,
  streamingMetrics: {
    connectionHealth: string;
    chunksReceived: number;
    totalBytes?: number;
    lastChunkTime?: number;
  } | null
): string => {
  if (isBackendOffline) return 'Offline - Limited functionality';

  if (isLoading && processingStatus) {
    const statusLower = processingStatus.toLowerCase();

    // Priority status indicators (errors take precedence)
    if (statusLower.includes('error') || statusLower.includes('failed')) {
      return `${processingStatus} ❌`;
    }
    if (statusLower.includes('timeout')) {
      return `${processingStatus} ⏰`;
    }
    if (statusLower.includes('cancelled') || statusLower.includes('aborted')) {
      return `${processingStatus} 🚫`;
    }
    if (statusLower.includes('degraded') || statusLower.includes('fallback')) {
      return `${processingStatus} ⚠️`;
    }

    // Connection health indicators with streaming metrics
    if (streamingMetrics) {
      const { connectionHealth, chunksReceived, totalBytes } = streamingMetrics;

      // Enhanced health icons with more granularity
      const healthIcons = {
        excellent: '🟢',
        good: '🟡',
        poor: '🟠',
        critical: '🔴',
        unknown: '⚪'
      };

      const healthIcon = healthIcons[connectionHealth as keyof typeof healthIcons] || '💭';

      // Show chunk count for active streaming
      if (chunksReceived > 0) {
        const bytesFormatted = totalBytes ? formatBytes(totalBytes) : '';
        const bytesText = bytesFormatted ? ` • ${bytesFormatted}` : '';
        return `${healthIcon} ${processingStatus} (${chunksReceived} chunks${bytesText})`;
      }

      return `${healthIcon} ${processingStatus}`;
    }

    // Default processing indicator
    return `${processingStatus} 💭`;
  }

  return '';
};

// Helper function to format bytes
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};