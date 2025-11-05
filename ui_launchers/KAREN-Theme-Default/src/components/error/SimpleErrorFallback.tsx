"use client";

import React from 'react';

export default function SimpleErrorFallback() {
  return (
    <div>
      <h3>SimpleErrorFallback</h3>
      <p>This component is temporarily disabled for production build.</p>
    </div>
  );
}

export { SimpleErrorFallback };