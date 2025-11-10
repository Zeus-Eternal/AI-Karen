/**
 * License Compliance Panel - Production Grade
 */
"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge, type BadgeProps } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';

export interface LicenseInfo { model: string; license: string; compliance: 'compliant' | 'review' | 'violation'; restrictions: string[]; }
export interface LicenseCompliancePanelProps { licenses: LicenseInfo[]; className?: string; }

const complianceVariantMap: Record<LicenseInfo['compliance'], NonNullable<BadgeProps['variant']>> = {
  compliant: 'default',
  review: 'secondary',
  violation: 'destructive',
};

export default function LicenseCompliancePanel({ licenses, className = '' }: LicenseCompliancePanelProps) {
  const violations = licenses.filter(l => l.compliance === 'violation');
  const needsReview = licenses.filter(l => l.compliance === 'review');
  
  return (
    <Card className={className}>
      <CardHeader><CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" />License Compliance</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        {violations.length > 0 && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{violations.length} license violation(s) detected</AlertDescription>
          </Alert>
        )}
        {needsReview.length > 0 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{needsReview.length} license(s) need review</AlertDescription>
          </Alert>
        )}
        <div className="space-y-2">
          {licenses.map(l => (
            <div key={l.model} className="flex items-start justify-between p-3 border rounded">
              <div>
                <div className="font-medium">{l.model}</div>
                <div className="text-sm text-muted-foreground">{l.license}</div>
                {l.restrictions.length > 0 && (
                  <div className="text-xs text-muted-foreground mt-1">{l.restrictions.join(', ')}</div>
                )}
              </div>
                <Badge variant={complianceVariantMap[l.compliance]}>
                {l.compliance === 'compliant' && <CheckCircle2 className="h-3 w-3 mr-1" />}
                {l.compliance}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export { LicenseCompliancePanel };
