import { AlertTriangle } from 'lucide-react';

interface CircuitBreakerWarningProps {
  show: boolean;
  reason?: string;
}

export default function CircuitBreakerWarning({ show, reason }: CircuitBreakerWarningProps) {
  if (!show) return null;

  return (
    <div className="mx-4 mb-3 rounded-md border border-amber-400/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-900 dark:text-amber-200">
      <div className="flex items-center gap-2 font-medium">
        <AlertTriangle className="h-4 w-4" />
        Circuit breaker or dependency degradation detected
      </div>
      {reason ? <div className="mt-1 opacity-90">{reason}</div> : null}
    </div>
  );
}
