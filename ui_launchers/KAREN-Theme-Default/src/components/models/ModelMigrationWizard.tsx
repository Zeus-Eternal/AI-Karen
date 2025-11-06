/**
 * Model Migration Wizard - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

export interface MigrationStep { id: string; title: string; status: 'pending' | 'active' | 'complete'; }
export interface ModelMigrationWizardProps { sourceModel: string; targetModel: string; onComplete?: () => void; className?: string; }

export default function ModelMigrationWizard({ sourceModel, targetModel, onComplete, className = '' }: ModelMigrationWizardProps) {
  const [steps, setSteps] = useState<MigrationStep[]>([
    { id: '1', title: 'Backup current configuration', status: 'pending' },
    { id: '2', title: 'Validate compatibility', status: 'pending' },
    { id: '3', title: 'Migrate settings', status: 'pending' },
    { id: '4', title: 'Test new model', status: 'pending' },
    { id: '5', title: 'Complete migration', status: 'pending' }
  ]);
  
  const activeIndex = steps.findIndex(s => s.status !== 'complete');
  const progress = (steps.filter(s => s.status === 'complete').length / steps.length) * 100;
  
  const nextStep = () => {
    const newSteps = [...steps];
    const activeIdx = newSteps.findIndex(s => s.status === 'pending');
    if (activeIdx >= 0) {
      newSteps[activeIdx].status = 'complete';
      if (activeIdx < newSteps.length - 1) {
        newSteps[activeIdx + 1].status = 'active';
      }
      setSteps(newSteps);
      if (activeIdx === newSteps.length - 1) {
        onComplete?.();
      }
    }
  };
  
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Model Migration Wizard</CardTitle>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>{sourceModel}</span>
          <ArrowRight className="h-4 w-4" />
          <span>{targetModel}</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress value={progress} />
        <div className="space-y-2">
          {steps.map((step, i) => (
            <div key={step.id} className="flex items-center justify-between p-3 border rounded">
              <div className="flex items-center gap-3">
                {step.status === 'complete' ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : (
                  <div className="h-5 w-5 rounded-full border-2 border-muted" />
                )}
                <span className={step.status === 'active' ? 'font-medium' : ''}>{step.title}</span>
              </div>
              <Badge variant={step.status === 'complete' ? 'default' : 'secondary'}>{step.status}</Badge>
            </div>
          ))}
        </div>
        {activeIndex < steps.length && (
          <Button onClick={nextStep} className="w-full">Continue</Button>
        )}
      </CardContent>
    </Card>
  );
}

export { ModelMigrationWizard };
