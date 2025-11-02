'use client';

import { useState, useEffect } from 'react';

export default function TestPage() {
  const [status, setStatus] = useState('Loading...');
  const [authStatus, setAuthStatus] = useState('Checking...');

  useEffect(() => {
    // Test basic functionality
    setStatus('Page loaded successfully!');
    
    // Test API connectivity
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        console.log('Health check:', data);
        setStatus(`API connected! Status: ${data.status}`);
      })
      .catch(err => {
        console.error('API error:', err);
        setStatus(`API error: ${err.message}`);
      });

    // Test authentication
    fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'test@example.com', password: 'test123' })
    })
      .then(res => res.json())
      .then(data => {
        console.log('Auth test:', data);
        if (data.access_token) {
          setAuthStatus('Authentication working!');
        } else {
          setAuthStatus(`Auth failed: ${data.error || 'Unknown error'}`);
        }
      })
      .catch(err => {
        console.error('Auth error:', err);
        setAuthStatus(`Auth error: ${err.message}`);
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <h1 className="text-2xl font-bold mb-4 text-gray-800">Karen AI Test Page</h1>
        <div className="space-y-4">
          <div>
            <h2 className="font-semibold text-gray-700">Frontend Status:</h2>
            <p className="text-green-600">{status}</p>
          </div>
          <div>
            <h2 className="font-semibold text-gray-700">Authentication Status:</h2>
            <p className="text-blue-600">{authStatus}</p>
          </div>
          <div className="mt-6">
            <a 
              href="/" 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              Go to Main App
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}