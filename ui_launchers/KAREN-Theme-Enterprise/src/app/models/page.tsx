"use client";

import * as React from 'react';
import { ModelBrowser } from '@/components/models';

export default function ModelsPage() {
  return (
    <div className="container mx-auto py-6">
      <ModelBrowser />
    </div>
  );
}