'use client';

import React from 'react';
import type { SetupStepProps } from '../SetupWizard';

type WelcomeStepProps = SetupStepProps;

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <div>
      <h2>Welcome</h2>
      <p>Temporarily disabled for build</p>
      <Button onClick={onNext}>Get Started</Button>
    </div>
  );
}
