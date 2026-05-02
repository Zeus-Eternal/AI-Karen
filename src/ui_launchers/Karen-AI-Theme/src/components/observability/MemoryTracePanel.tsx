import { MemoryObservabilitySummary } from '@/lib/memory-observability';

export function MemoryTracePanel({ summary }: { summary: MemoryObservabilitySummary }) {
  return <div className='grid grid-cols-2 gap-2 text-xs'>
    <div>Memory Used: <strong>{summary.memory_used ? 'yes' : 'no'}</strong></div>
    <div>Activation Mode: <strong>{summary.activation_mode ?? 'n/a'}</strong></div>
    <div>Memory Classes: <strong>{(summary.memory_classes ?? []).join(', ') || 'n/a'}</strong></div>
    <div>Stores Queried: <strong>{(summary.stores_queried ?? []).join(', ') || 'n/a'}</strong></div>
    <div>Selected Memories: <strong>{summary.selected_count ?? 0}</strong></div>
    <div>Token Budget Used: <strong>{summary.token_budget ?? 'n/a'}</strong></div>
    <div>Degraded: <strong>{summary.degraded ? 'yes' : 'no'}</strong></div>
    <div>Writeback Status: <strong>{summary.writeback_status ?? 'n/a'}</strong></div>
  </div>;
}
