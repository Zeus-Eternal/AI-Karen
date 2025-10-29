'use client';

import React, { useState } from 'react';
import { testClipboardWithUserInteraction } from '@/utils/text-selection-test';

interface ClipboardTestProps {
  className?: string;
}

export function ClipboardTest({ className = '' }: ClipboardTestProps) {
  const [testResult, setTestResult] = useState<{
    success: boolean;
    error?: string;
    tested: boolean;
  }>({ success: false, tested: false });

  const handleTestClipboard = async () => {
    const result = await testClipboardWithUserInteraction();
    setTestResult({
      success: result.success,
      error: result.error,
      tested: true,
    });
  };

  return (
    <div className={`clipboard-test ${className}`}>
      <div className="flex items-center gap-4 p-4 border rounded-lg">
        <button
          onClick={handleTestClipboard}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Test Clipboard
        </button>
        
        {testResult.tested && (
          <div className={`flex items-center gap-2 ${
            testResult.success ? 'text-green-600' : 'text-red-600'
          }`}>
            <span className="text-lg">
              {testResult.success ? '✅' : '❌'}
            </span>
            <span>
              {testResult.success 
                ? 'Clipboard working!' 
                : `Clipboard failed: ${testResult.error}`
              }
            </span>
          </div>
        )}
      </div>
      
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">Test Instructions:</h3>
        <ol className="list-decimal list-inside space-y-1 text-sm">
          <li>Click the "Test Clipboard" button above</li>
          <li>The test will attempt to write and read from clipboard</li>
          <li>If successful, you'll see a green checkmark</li>
          <li>If it fails, check browser permissions and focus</li>
        </ol>
      </div>
    </div>
  );
}

export default ClipboardTest;