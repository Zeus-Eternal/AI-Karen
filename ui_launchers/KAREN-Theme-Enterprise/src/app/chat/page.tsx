"use client";
import React, { useState, useCallback } from 'react';
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import KarenChatInterface, { KarenMessage } from "@/components/chat/KarenChatInterface";
import KarenSidebar from "@/components/chat/KarenSidebar";
import { AppShell } from "@/components/layout/AppShell";
import { SidebarNavigation } from "@/components/navigation/SidebarNavigation";
import { Header as ModernHeader } from "@/components/layout/ModernHeader";
import { ErrorBoundary } from "@/components/ui/error-boundary";

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('ChatView Error Boundary caught an error:', error, errorInfo);
        }}
        fallback={
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-center p-6 bg-red-50 border border-red-200 rounded-lg max-w-md">
              <h2 className="text-xl font-semibold text-red-800 mb-2">Chat Interface Error</h2>
              <p className="text-red-600 mb-4">
                There was an error loading the chat interface. Please try refreshing the page.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                Refresh Page
              </button>
            </div>
          </div>
        }
      >
        <ChatView />
      </ErrorBoundary>
    </ProtectedRoute>
  );
}

function ChatView() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<KarenMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m Karen AI, your intelligent assistant. How can I help you today?',
      timestamp: new Date(),
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSidebarToggle = useCallback(() => {
    setSidebarOpen(prev => !prev);
  }, []);

  const handleSendMessage = useCallback(async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message
    const userMessage: KarenMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: KarenMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `I understand you said: "${message}". This is a demonstration of the production-ready chat interface.`,
        timestamp: new Date(),
        metadata: {
          confidence: 0.95,
          intent: 'chat'
        }
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  }, [isLoading]);

  return (
    <AppShell
      sidebar={<SidebarNavigation />}
      header={<ModernHeader title="Chat Studio" showSearch={false} />}
      className="min-h-screen"
    >
      <div className="flex flex-1 flex-col gap-6 px-4 py-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <div className="order-2 lg:order-1">
            <KarenSidebar
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
            />
          </div>
          <div className="order-1 lg:order-2">
            <KarenChatInterface
              messages={messages}
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
              sidebarOpen={sidebarOpen}
              onSidebarToggle={handleSidebarToggle}
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
