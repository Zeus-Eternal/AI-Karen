import { Badge } from '@/components/ui/badge';

export function MemoryEventBadge({ status }: { status: string }) {
  const variant = status === 'completed' ? 'secondary' : status === 'failed' ? 'destructive' : 'outline';
  return <Badge variant={variant}>{status}</Badge>;
}
