import { MemoryObservabilityEvent } from '@/lib/memory-observability';
import { MemoryEventBadge } from './MemoryEventBadge';

export function MemoryActivityTimeline({ events }: { events: MemoryObservabilityEvent[] }) {
  return <div className='space-y-2'>{events.map((e, i) => <div key={i} className='rounded border p-2 text-xs flex justify-between'><div><div>{e.event_name}</div><div className='text-muted-foreground'>{e.store} {e.latency_ms ? `• ${e.latency_ms}ms` : ''}</div></div><div className='text-right'><MemoryEventBadge status={e.status} /><div>{e.result_count ?? 0}/{e.selected_count ?? 0}</div></div></div>)}</div>;
}
