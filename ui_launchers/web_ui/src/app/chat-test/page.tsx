'use client';

import React from 'react';
import { ChatInterface } from '@/components/ChatInterface';

export default function ChatTestPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Chat Test (No Auth)</h1>
        <ChatInterface />
      </div>
    </div>
  );
}