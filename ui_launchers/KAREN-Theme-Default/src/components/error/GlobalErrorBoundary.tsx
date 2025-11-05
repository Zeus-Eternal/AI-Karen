"use client";

import React from 'react';

export default function GlobalErrorBoundary({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export { GlobalErrorBoundary };