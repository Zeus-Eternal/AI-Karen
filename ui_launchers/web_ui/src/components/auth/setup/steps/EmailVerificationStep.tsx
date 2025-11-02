'use client';

import React from 'react';
import type { SetupStepProps } from '../SetupWizard';

type EmailVerificationStepProps = SetupStepProps;

export function EmailVerificationStep({ onNext, onPrevious }: EmailVerificationStepProps) {
  return (
    <div>
      <h2>Email Verification Step</h2>
      <p>Temporarily disabled for build</p>
      <button onClick={onNext}>Next</button>
      <button onClick={onPrevious}>Back</button>
    </div>
  );
}
