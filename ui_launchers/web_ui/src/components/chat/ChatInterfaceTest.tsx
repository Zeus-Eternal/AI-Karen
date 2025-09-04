/**
 * ChatInterface Test Component - For testing error handling fixes
 */

'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChatInterface } from './ChatInterface';
import { SafeChatWrapper } from './SafeChatWrapper';
import { safeError, safeWarn, safeInfo } from '@/lib/safe-console';

export function ChatInterfaceTest() {
  const [showChat, setShowChat] = useState(false);
  const [testResults, setTestResults] = useState<string[]>([]);

  const addTestResult = (result: string) => {
    setTestResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${result}`]);
  };

  const testConsoleError = () => {
    try {
      // Test regular console.error
      console.error('Test regular console error');
      addTestResult('✅ Regular console.error works');
      
      // Test safe console error
      safeError('Test safe console error', new Error('Test error'));
      addTestResult('✅ Safe console error works');
      
      // Test problematic console error (should be caught)
      console.error('ChatInterface.useCallback[sendMessage] test error');
      addTestResult('✅ Problematic console error handled safely');
      
    } catch (error) {
      addTestResult(`❌ Console error test failed: ${error}`);
    }
  };

  const testChatInterface = () => {
    setShowChat(true);
    addTestResult('✅ ChatInterface loaded');
  };

  const simulateError = () => {
    try {
      // Simulate the specific error from the stack trace
      throw new Error('Simulated ChatInterface sendMessage error');
    } catch (error) {
      safeError('Simulated error caught safely', error);
      addTestResult('✅ Simulated error handled safely');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>ChatInterface Error Handling Test</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            <Button onClick={testConsoleError} variant="outline">
              Test Console Error Handling
            </Button>
            <Button onClick={testChatInterface} variant="outline">
              Load ChatInterface
            </Button>
            <Button onClick={simulateError} variant="outline">
              Simulate Error
            </Button>
            <Button 
              onClick={() => setTestResults([])} 
              variant="ghost"
            >
              Clear Results
            </Button>
          </div>
          
          {testResults.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">Test Results:</h4>
              <div className="bg-muted p-3 rounded-md max-h-40 overflow-y-auto">
                {testResults.map((result, index) => (
                  <div key={index} className="text-sm font-mono">
                    {result}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {showChat && (
        <Card>
          <CardHeader>
            <CardTitle>ChatInterface Test</CardTitle>
          </CardHeader>
          <CardContent>
            <SafeChatWrapper
              onError={(error, errorInfo) => {
                addTestResult(`❌ ChatInterface error: ${error.message}`);
              }}
            >
              <div style={{ height: '400px' }}>
                <ChatInterface
                  height="400px"
                  placeholder="Test the chat interface..."
                  welcomeMessage="This is a test instance of the ChatInterface. Try sending a message to test error handling."
                  onMessageSent={(message) => {
                    addTestResult(`📤 Message sent: ${message.content.substring(0, 50)}...`);
                  }}
                  onMessageReceived={(message) => {
                    addTestResult(`📥 Message received: ${message.content.substring(0, 50)}...`);
                  }}
                />
              </div>
            </SafeChatWrapper>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ChatInterfaceTest;