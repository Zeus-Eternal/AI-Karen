"use client";

import React, { useState, useEffect } from 'react';
import { getConfigManager } from '@/lib/endpoint-config';

interface ConnectionTest {
  endpoint: string;
  status: 'pending' | 'success' | 'error';
  responseTime?: number;
  error?: string;
}

export function ConnectionDiagnostic() {
  const [tests, setTests] = useState<ConnectionTest[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runDiagnostics = async () => {
    setIsRunning(true);
    const endpoints = [
      { name: 'Backend Direct', url: 'http://localhost:8000/api/health' },
      { name: 'Proxy Health', url: '/api/health' },
      { name: 'Proxy Chat Runtime', url: '/api/chat/proxy?path=/api/chat/runtime' },
      { name: 'Backend Chat Runtime', url: 'http://localhost:8000/api/chat/runtime' },
    ];

    const testResults: ConnectionTest[] = [];

    for (const endpoint of endpoints) {
      const test: ConnectionTest = {
        endpoint: `${endpoint.name}: ${endpoint.url}`,
        status: 'pending'
      };
      testResults.push(test);
      setTests([...testResults]);

      try {
        const startTime = performance.now();
        const response = await fetch(endpoint.url, {
          method: endpoint.url.includes('/chat/runtime') ? 'POST' : 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          body: endpoint.url.includes('/chat/runtime') 
            ? JSON.stringify({ message: 'test', stream: false })
            : undefined,
        });

        const responseTime = performance.now() - startTime;
        
        if (response.ok) {
          test.status = 'success';
          test.responseTime = responseTime;
        } else {
          test.status = 'error';
          test.error = `HTTP ${response.status}: ${response.statusText}`;
        }
      } catch (error) {
        test.status = 'error';
        test.error = error instanceof Error ? error.message : 'any error';
      }

      setTests([...testResults]);
    }

    setIsRunning(false);
  };

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      void runDiagnostics();
    });

    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Connection Diagnostics</h3>
        <button
          onClick={runDiagnostics}
          disabled={isRunning}
          className="px-3 py-1 bg-blue-500 text-white rounded disabled:opacity-50"
        >
          {isRunning ? 'Running...' : 'Run Tests'}
        </button>
      </div>

      <div className="space-y-2">
        {tests.map((test, index) => (
          <div key={index} className="flex items-center justify-between p-2 bg-white rounded border">
            <span className="font-mono text-sm">{test.endpoint}</span>
            <div className="flex items-center space-x-2">
              {test.responseTime && (
                <span className="text-xs text-gray-500">{test.responseTime.toFixed(0)}ms</span>
              )}
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                test.status === 'success' ? 'bg-green-100 text-green-800' :
                test.status === 'error' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {test.status === 'success' ? '✓ Success' :
                 test.status === 'error' ? '✗ Error' :
                 '⏳ Testing...'}
              </span>
            </div>
            {test.error && (
              <div className="text-xs text-red-600 mt-1">{test.error}</div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 text-xs text-gray-600">
        <p>Configuration: {JSON.stringify(getConfigManager().getEnvironmentInfo(), null, 2)}</p>
      </div>
    </div>
  );
}
