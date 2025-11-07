'use client';

import React from 'react';
import { Button } from "@/components/ui/button";
import type { SetupStepProps } from '../SetupWizard';

export type SetupCompleteStepProps = SetupStepProps & {
  onComplete: () => void | Promise<void>;
};

export function SetupCompleteStep({ onComplete, onPrevious }: SetupCompleteStepProps) {
  return (
    <div>
      <h2>Setup Complete</h2>
      <p>Temporarily disabled for build</p>
      <Button onClick={onComplete}>Finish</Button>
      <Button onClick={onPrevious}>Back</Button>
    </div>
  );
}
