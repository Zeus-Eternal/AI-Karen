import MemoryEventTable from './MemoryEventTable';
import MemoryCircuitBreakerPanel from './MemoryCircuitBreakerPanel';
import MemoryLatencyChart from './MemoryLatencyChart';
import { MemoryObservabilityEvent, MemoryObservabilitySummary } from '@/lib/memory-observability';
import { MemoryCenterPanel } from '@/components/observability/MemoryCenterPanel';

export default function MemoryObservabilityDashboard({ events, summary }: { events: MemoryObservabilityEvent[]; summary: MemoryObservabilitySummary }) {
  return <div className='space-y-4'><MemoryCircuitBreakerPanel state={summary.circuit_breaker_state} /><MemoryCenterPanel events={events} summary={summary} /><MemoryLatencyChart latencies={summary.store_latencies_ms} /><MemoryEventTable events={events} /></div>;
}
