'use client';

import React from 'react';
import type { SetupStepProps } from '../SetupWizard';

type SetupCompleteStepProps = SetupStepProps & {
  onComplete: () => void | Promise<void>;
};

export function SetupCompleteStep({ onComplete, onPrevious }: SetupCompleteStepProps) {
  return (
    <div>
      <h2>Setup Complete</h2>
      <p>Temporarily disabled for build</p>
      <button onClick={onComplete}>Finish</button>
      <button onClick={onPrevious}>Back</button>
    </div>
  );
}
