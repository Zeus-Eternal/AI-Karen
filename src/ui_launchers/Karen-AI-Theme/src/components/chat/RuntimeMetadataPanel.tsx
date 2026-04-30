import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface RuntimeMetadataPanelProps {
  requestedProvider?: string;
  actualProvider?: string;
  requestedModel?: string;
  actualModel?: string;
  runtimeEngine?: string;
  fallbackLevel?: string;
  correlationId?: string;
  requestId?: string;
  status?: string;
}

const safe = (value?: string) => (value && value.trim() ? value : 'n/a');

export default function RuntimeMetadataPanel(props: RuntimeMetadataPanelProps) {
  return (
    <Card className="mx-4 mb-3 border-primary/20 bg-card/70">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">Runtime Metadata</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4">
        <div><span className="text-muted-foreground">Requested Provider:</span> <strong>{safe(props.requestedProvider)}</strong></div>
        <div><span className="text-muted-foreground">Actual Provider:</span> <strong>{safe(props.actualProvider)}</strong></div>
        <div><span className="text-muted-foreground">Requested Model:</span> <strong>{safe(props.requestedModel)}</strong></div>
        <div><span className="text-muted-foreground">Actual Model:</span> <strong>{safe(props.actualModel)}</strong></div>
        <div><span className="text-muted-foreground">Runtime Engine:</span> <strong>{safe(props.runtimeEngine)}</strong></div>
        <div><span className="text-muted-foreground">Fallback Level:</span> <strong>{safe(props.fallbackLevel)}</strong></div>
        <div><span className="text-muted-foreground">Correlation ID:</span> <code>{safe(props.correlationId)}</code></div>
        <div><span className="text-muted-foreground">Request ID:</span> <code>{safe(props.requestId)}</code></div>
        <div className="sm:col-span-2 lg:col-span-4">
          <Badge variant="outline">Status: {safe(props.status)}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}
