'use client';

import React from 'react';
import type { SetupStepProps } from '../SetupWizard';
import { Button } from "@/components/ui/button";

type EmailVerificationStepProps = SetupStepProps;

export function EmailVerificationStep({ onNext, onPrevious }: EmailVerificationStepProps) {
  return (
    <div>
      <h2>Email Verification Step</h2>
      <p>Temporarily disabled for build</p>
      <Button onClick={onNext}>Next</Button>
      <Button onClick={onPrevious}>Back</Button>
    </div>
  );
}
