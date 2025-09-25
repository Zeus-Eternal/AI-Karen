/**
 * Session Persistence Test Page
 * 
 * This page helps test and debug session persistence issues.
 * It shows the current session state and provides buttons to test various scenarios.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useSession } from '@/contexts/SessionProvider';
import { getApiClient } from '@/lib/api-client';
import { getSession, clearSession, bootSession, refreshToken, isAuthenticated } from '@/lib/auth/session';

interface SessionTestResult {
  timestamp: string;
  test: string;
  success: boolean;
  message: string;
  data?: any;
}

export default function TestSessionPage() {
  const { 
    isAuthenticated: contextAuthenticated, 
    user, 
    isLoading, 
    refreshSession,
    attemptRecovery 
  } = useSession();
  
  const [testResults, setTestResults] = useState<SessionTestResult[]>([]);
  const [sessionData, setSessionData] = useState<any>(null);
  const [isRunningTest, setIsRunningTest] = useState(false);

  // Update session data display
  useEffect(() => {
    const updateSessionData = () => {
      const session = getSession();
      setSessionData({
        session,
        isAuthenticated: isAuthenticated(),
        contextAuthenticated,
        user,
        cookies: typeof document !== 'undefined' ? document.cookie : 'N/A'
      });
    };

    updateSessionData();
    const interval = setInterval(updateSessionData, 1000);
    return () => clearInterval(interval);
  }, [contextAuthenticated, user]);

  const addTestResult = (test: string, success: boolean, message: string, data?: any) => {
    const result: SessionTestResult = {
      timestamp: new Date().toISOString(),
      test,
      success,
      message,
      data
    };
    setTestResults(prev => [result, ...prev.slice(0, 9)]); // Keep last 10 results
  };

  const testSessionValidation = async () => {
    setIsRunningTest(true);
    try {
      const apiClient = getApiClient();
      const response = await apiClient.get('/api/auth/validate-session');
      
      addTestResult(
        'Session Validation',
        response.data.valid,
        response.data.valid ? 'Session is valid' : response.data.error,
        response.data
      );
    } catch (error: any) {
      addTestResult('Session Validation', false, error.message);
    } finally {
      setIsRunningTest(false);
    }
  };

  const testTokenRefresh = async () => {
    setIsRunningTest(true);
    try {
      await refreshToken();
      addTestResult('Token Refresh', true, 'Token refreshed successfully');
      refreshSession();
    } catch (error: any) {
      addTestResult('Token Refresh', false, error.message);
    } finally {
      setIsRunningTest(false);
    }
  };

  const testBootSession = async () => {
    setIsRunningTest(true);
    try {
      await bootSession();
      addTestResult('Boot Session', true, 'Session booted successfully');
      refreshSession();
    } catch (error: any) {
      addTestResult('Boot Session', false, error.message);
    } finally {
      setIsRunningTest(false);
    }
  };

  const testSessionRecovery = async () => {
    setIsRunningTest(true);
    try {
      const result = await attemptRecovery();
      addTestResult(
        'Session Recovery',
        result.success,
        result.message || (result.success ? 'Recovery successful' : 'Recovery failed'),
        result
      );
    } catch (error: any) {
      addTestResult('Session Recovery', false, error.message);
    } finally {
      setIsRunningTest(false);
    }
  };

  const testClearSession = () => {
    clearSession();
    addTestResult('Clear Session', true, 'Session cleared from memory');
    refreshSession();
  };

  const testProtectedEndpoint = async () => {
    setIsRunningTest(true);
    try {
      const apiClient = getApiClient();
      const response = await apiClient.get('/api/auth/me');
      
      addTestResult(
        'Protected Endpoint',
        true,
        'Successfully accessed protected endpoint',
        response.data
      );
    } catch (error: any) {
      addTestResult('Protected Endpoint', false, error.message);
    } finally {
      setIsRunningTest(false);
    }
  };

  const clearTestResults = () => {
    setTestResults([]);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Session Persistence Test</h1>
          
          {/* Session Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-3">Session Status</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Context Authenticated:</span>
                  <span className={contextAuthenticated ? 'text-green-600' : 'text-red-600'}>
                    {contextAuthenticated ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Memory Authenticated:</span>
                  <span className={isAuthenticated() ? 'text-green-600' : 'text-red-600'}>
                    {isAuthenticated() ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>User Email:</span>
                  <span>{user?.email || 'None'}</span>
                </div>
                <div className="flex justify-between">
                  <span>User ID:</span>
                  <span>{user?.userId || 'None'}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-3">Session Data</h2>
              <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-32">
                {JSON.stringify(sessionData, null, 2)}
              </pre>
            </div>
          </div>

          {/* Test Controls */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">Test Controls</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button
                onClick={testSessionValidation}
                disabled={isRunningTest}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Validate Session
              </button>
              <button
                onClick={testTokenRefresh}
                disabled={isRunningTest}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                Refresh Token
              </button>
              <button
                onClick={testBootSession}
                disabled={isRunningTest}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
              >
                Boot Session
              </button>
              <button
                onClick={testSessionRecovery}
                disabled={isRunningTest}
                className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
              >
                Session Recovery
              </button>
              <button
                onClick={testProtectedEndpoint}
                disabled={isRunningTest}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                Protected Endpoint
              </button>
              <button
                onClick={testClearSession}
                disabled={isRunningTest}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
              >
                Clear Session
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Reload Page
              </button>
              <button
                onClick={clearTestResults}
                className="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500"
              >
                Clear Results
              </button>
            </div>
          </div>

          {/* Test Results */}
          <div>
            <h2 className="text-lg font-semibold mb-3">Test Results</h2>
            {testResults.length === 0 ? (
              <p className="text-gray-500">No test results yet. Run some tests above.</p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-auto">
                {testResults.map((result, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded border-l-4 ${
                      result.success 
                        ? 'bg-green-50 border-green-400' 
                        : 'bg-red-50 border-red-400'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium">{result.test}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(result.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{result.message}</p>
                    {result.data && (
                      <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-20">
                        {JSON.stringify(result.data, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-3">Testing Instructions</h2>
          <div className="text-sm text-blue-800 space-y-2">
            <p><strong>1. Login Test:</strong> Make sure you're logged in first</p>
            <p><strong>2. Refresh Test:</strong> Reload the page and check if session persists</p>
            <p><strong>3. Token Refresh:</strong> Test automatic token refresh functionality</p>
            <p><strong>4. Session Recovery:</strong> Clear session and test recovery</p>
            <p><strong>5. Protected Endpoint:</strong> Test access to authenticated endpoints</p>
          </div>
        </div>
      </div>
    </div>
  );
}