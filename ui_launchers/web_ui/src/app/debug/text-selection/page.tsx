import React from 'react';
import TextSelectionTest from '@/components/debug/TextSelectionTest';

export default function TextSelectionDebugPage() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <TextSelectionTest />
      </div>
    </div>
  );
}