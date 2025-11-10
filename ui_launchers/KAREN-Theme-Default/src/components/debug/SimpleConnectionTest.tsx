"use client";

import React, { useState } from 'react';

export function SimpleConnectionTest() {
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    setResult('Testing...');

    try {
      // Test the proxy endpoint directly
      const response = await fetch('/api/chat/proxy?path=/api/chat/runtime', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Simple test message',
          stream: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(`Success! Response: ${data.content}`);
    } catch (error) {
      setResult(`Error: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Simple Connection Test</h3>
      <button
        onClick={testConnection}
        disabled={loading}
        className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50 mb-4"
      >
        {loading ? 'Testing...' : 'Test Connection'}
      </button>
      <div className="bg-gray-100 p-3 rounded">
        <pre className="text-sm whitespace-pre-wrap">{result}</pre>
      </div>
    </div>
  );
}