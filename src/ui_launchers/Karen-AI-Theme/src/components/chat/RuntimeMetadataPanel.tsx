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

export default function RuntimeMetadataPanel(props: RuntimeMetadataPanelProps) {
  const fields: Array<{ label: string; value?: string; mono?: boolean }> = [
    { label: 'Requested Provider', value: props.requestedProvider },
    { label: 'Actual Provider', value: props.actualProvider },
    { label: 'Requested Model', value: props.requestedModel },
    { label: 'Actual Model', value: props.actualModel },
    { label: 'Runtime Engine', value: props.runtimeEngine },
    { label: 'Fallback Level', value: props.fallbackLevel },
    { label: 'Correlation ID', value: props.correlationId, mono: true },
    { label: 'Request ID', value: props.requestId, mono: true },
  ].filter((field) => Boolean(field.value && field.value.trim()));

  if (!fields.length && !(props.status && props.status.trim())) {
    return null;
  }

  return (
    <Card className="mx-4 mb-3 border-primary/20 bg-card/70">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">Runtime Metadata</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4">
        {fields.map((field) => (
          <div key={field.label}>
            <span className="text-muted-foreground">{field.label}:</span>{' '}
            {field.mono ? <code>{field.value}</code> : <strong>{field.value}</strong>}
          </div>
        ))}
        {props.status && props.status.trim() ? (
          <div className="sm:col-span-2 lg:col-span-4">
            <Badge variant="outline">Status: {props.status.trim()}</Badge>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
