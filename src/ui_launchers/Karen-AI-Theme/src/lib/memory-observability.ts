export type MemoryObservabilityEvent = {
  event_name: string;
  status: 'running' | 'completed' | 'skipped' | 'failed' | 'degraded';
  latency_ms?: number;
  degradation_reason?: string | null;
  store?: string | null;
  result_count?: number;
  selected_count?: number;
};

export type MemoryObservabilitySummary = {
  memory_used: boolean;
  activation_mode?: string;
  memory_classes?: string[];
  stores_queried?: string[];
  store_latencies_ms?: Record<string, number>;
  result_count?: number;
  selected_count?: number;
  token_budget?: number;
  degraded?: boolean;
  degradation_reason?: string | null;
  circuit_breaker_state?: string;
  writeback_status?: string;
};

export const mapEventToStageLabel = (name: string): string => {
  const key = name.toLowerCase();
  if (key.includes('activation')) return 'Checking memory activation...';
  if (key.includes('milvus')) return 'Querying Milvus memory...';
  if (key.includes('elastic')) return 'Querying Elasticsearch memory...';
  if (key.includes('fusion')) return 'Fusing recall results...';
  if (key.includes('profile')) return 'Checking profile facts...';
  if (key.includes('guard')) return 'Running memory guard...';
  if (key.includes('writeback')) return 'Saving useful context...';
  if (key.includes('projection')) return 'Projection completed.';
  return 'Searching recent context...';
};
