import { MemoryObservabilityEvent } from '@/lib/memory-observability';

export default function MemoryEventTable({ events }: { events: MemoryObservabilityEvent[] }) {
  return <table className='w-full text-xs'><thead><tr><th>Event</th><th>Status</th><th>Store</th><th>Latency</th></tr></thead><tbody>{events.map((e,i)=><tr key={i}><td>{e.event_name}</td><td>{e.status}</td><td>{e.store ?? '-'}</td><td>{e.latency_ms ?? '-'}</td></tr>)}</tbody></table>;
}
