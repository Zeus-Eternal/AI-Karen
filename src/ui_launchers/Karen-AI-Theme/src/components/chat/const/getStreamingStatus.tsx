export const getStreamingStatus = (
  isBackendOffline: boolean,
  isLoading: boolean,
  processingStatus: string,
  streamingMetrics: { connectionHealth: string; chunksReceived: number } | null
): string => {
  if (isBackendOffline) return 'Offline - Limited functionality';
  if (isLoading && processingStatus) {
    // Add visual indicators for different status types
    const statusLower = processingStatus.toLowerCase();
    if (statusLower.includes('degraded')) return `${processingStatus} ⚠️`;
    if (statusLower.includes('error')) return `${processingStatus} ❌`;
    if (statusLower.includes('timeout')) return `${processingStatus} ⏰`;
    if (statusLower.includes('cancelled')) return `${processingStatus} 🚫`;

    // Add connection health indicators
    if (streamingMetrics) {
      const { connectionHealth, chunksReceived } = streamingMetrics;
      const healthIcons = {
        excellent: '💚',
        good: '💛',
        poor: '🧡',
        critical: '❤️'
      };
      const healthIcon = healthIcons[connectionHealth as keyof typeof healthIcons] || '💭';
      return `${healthIcon} ${processingStatus} (${chunksReceived} chunks)`;
    }

    return `${processingStatus} 💭`;
  }
  return '';
};