'use client';

import React from 'react';
import { SetupWizard } from '@/components/auth/setup/SetupWizard';
import { SetupRouteGuard } from '@/components/auth/setup/SetupRouteGuard';

export default function SetupPage() {
  return (
    <SetupRouteGuard>
      <SetupWizard />
    </SetupRouteGuard>
  );
}