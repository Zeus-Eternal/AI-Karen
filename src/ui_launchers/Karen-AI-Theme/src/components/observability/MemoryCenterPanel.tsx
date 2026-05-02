import { MemoryObservabilityEvent, MemoryObservabilitySummary } from '@/lib/memory-observability';
import { MemoryTracePanel } from './MemoryTracePanel';
import { MemoryActivityTimeline } from './MemoryActivityTimeline';

export function MemoryCenterPanel({ events, summary }: { events: MemoryObservabilityEvent[]; summary: MemoryObservabilitySummary }) {
  return (
    <section className="space-y-3 rounded-lg border p-3">
      <h3 className="text-sm font-semibold">Memory Center</h3>
      <MemoryTracePanel summary={summary} />
      <MemoryActivityTimeline events={events} />
    </section>
  );
}
