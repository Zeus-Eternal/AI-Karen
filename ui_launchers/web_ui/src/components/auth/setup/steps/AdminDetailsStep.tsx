'use client';

import React from 'react';
import type { SetupStepProps } from '../SetupWizard';

type AdminDetailsStepProps = SetupStepProps;

export function AdminDetailsStep({ onNext, onPrevious }: AdminDetailsStepProps) {
  return (
    <div>
      <h2>Admin Details Step</h2>
      <p>Temporarily disabled for build</p>
      <button onClick={onNext}>Next</button>
      <button onClick={onPrevious}>Back</button>
    </div>
  );
}
