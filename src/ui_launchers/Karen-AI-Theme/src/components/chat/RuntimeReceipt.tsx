import { Badge } from '@/components/ui/badge';

interface RuntimeReceiptProps {
  source?: string;
  usedFallback?: boolean;
  degradedReason?: string;
}

export default function RuntimeReceipt({ source, usedFallback, degradedReason }: RuntimeReceiptProps) {
  return (
    <div className="mx-4 mb-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
      <Badge variant="secondary">Source: {source || 'unknown'}</Badge>
      <Badge variant={usedFallback ? 'destructive' : 'outline'}>
        {usedFallback ? 'Fallback Used' : 'Primary Path'}
      </Badge>
      {degradedReason ? <Badge variant="outline">Reason: {degradedReason}</Badge> : null}
    </div>
  );
}
