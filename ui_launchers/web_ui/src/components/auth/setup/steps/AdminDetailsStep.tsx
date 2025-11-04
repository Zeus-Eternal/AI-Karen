'use client';

import React from 'react';
import type { SetupStepProps } from '../SetupWizard';

type AdminDetailsStepProps = SetupStepProps;

export function AdminDetailsStep({ onNext, onPrevious }: AdminDetailsStepProps) {
  return (
    <div>
      <h2>Admin Details Step</h2>
      <p>Temporarily disabled for build</p>
      <Button onClick={onNext}>Next</Button>
      <Button onClick={onPrevious}>Back</Button>
    </div>
  );
}
