import MemoryObservabilityDashboard from '@/components/admin/memory/MemoryObservabilityDashboard';

export default async function MemoryObservabilityPage() {
  const res: Response | null = await fetch('/api/admin/memory/observability', { cache: 'no-store' }).catch(() => null);
  const data = res && res.ok ? await res.json() : { events: [], summary: { memory_used: false } };
  return <main className='p-6'><h1 className='text-xl font-semibold mb-4'>Memory Observability</h1><MemoryObservabilityDashboard events={data.events ?? []} summary={data.summary ?? { memory_used: false }} /></main>;
}
