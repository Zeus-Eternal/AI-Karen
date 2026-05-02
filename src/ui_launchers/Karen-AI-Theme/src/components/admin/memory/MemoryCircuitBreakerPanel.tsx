export default function MemoryCircuitBreakerPanel({ state }: { state?: string }) {
  return <div className='rounded border p-3 text-sm'>Circuit Breaker State: <strong>{state ?? 'unknown'}</strong></div>;
}
