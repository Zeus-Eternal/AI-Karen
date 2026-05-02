export default function MemoryLatencyChart({ latencies }: { latencies?: Record<string, number> }) {
  const rows = Object.entries(latencies ?? {});
  return <div className='rounded border p-3 text-xs space-y-1'>{rows.map(([k,v]) => <div key={k}>{k}: {v}ms</div>)}</div>;
}
