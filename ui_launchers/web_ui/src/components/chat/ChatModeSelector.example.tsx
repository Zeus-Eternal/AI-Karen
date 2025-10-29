/**
 * ChatModeSelector Usage Example
 * 
 * This example demonstrates how to use the ChatModeSelector component
 * in a real application context.
 */

import React, { useState } from 'react';
import ChatModeSelector, { ChatMode, ChatContext } from './ChatModeSelector';
import { Model } from '@/lib/model-utils';

// Example usage component
export default function ChatModeSelectorExample() {
  const [currentMode, setCurrentMode] = useState<ChatMode>('text');
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [preserveContext, setPreserveContext] = useState(true);

  // Mock chat context
  const mockChatContext: ChatContext = {
    messages: [
      {
        id: '1',
        content: 'Hello, how are you?',
        type: 'user',
        mode: 'text',
        timestamp: new Date()
      },
      {
        id: '2',
        content: 'I am doing well, thank you for asking!',
        type: 'assistant',
        mode: 'text',
        modelUsed: 'gpt-4',
        timestamp: new Date()
      }
    ],
    currentTopic: 'General conversation',
    conversationLength: 2
  };

  const handleModeChange = (mode: ChatMode, model: Model | null) => {
    console.log('Mode changed to:', mode, 'with model:', model?.name);
    setCurrentMode(mode);
    setSelectedModel(model);
  };

  const handleModelChange = (model: Model | null) => {
    console.log('Model changed to:', model?.name);
    setSelectedModel(model);
  };

  const handleContextPreservationChange = (preserve: boolean) => {
    console.log('Context preservation:', preserve);
    setPreserveContext(preserve);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">ChatModeSelector Example</h1>
        <p className="text-gray-600">
          This example shows how the ChatModeSelector component works with different modes and models.
        </p>
      </div>

      <ChatModeSelector
        currentMode={currentMode}
        selectedModel={selectedModel}
        chatContext={mockChatContext}
        onModeChange={handleModeChange}
        onModelChange={handleModelChange}
        onContextPreservationChange={handleContextPreservationChange}
        className="w-full"
      />

      {/* Status Display */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="font-medium mb-2">Current Status:</h3>
        <ul className="space-y-1 text-sm">
          <li><strong>Mode:</strong> {currentMode}</li>
          <li><strong>Model:</strong> {selectedModel?.name || 'None selected'}</li>
          <li><strong>Context Preservation:</strong> {preserveContext ? 'Enabled' : 'Disabled'}</li>
          <li><strong>Conversation Length:</strong> {mockChatContext.conversationLength} messages</li>
        </ul>
      </div>

      {/* Usage Instructions */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="font-medium mb-2">How to Use:</h3>
        <ol className="list-decimal list-inside space-y-1 text-sm">
          <li>Select a chat mode (Text, Image, or Multi-modal)</li>
          <li>Choose a model from the dropdown for the selected mode</li>
          <li>If you have an active conversation, you'll see a confirmation dialog</li>
          <li>Choose whether to preserve conversation context during mode switches</li>
          <li>Use the Quick Switch button to automatically select the optimal model</li>
        </ol>
      </div>

      {/* Features */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="font-medium mb-2">Key Features:</h3>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>Automatic mode adaptation based on selected model capabilities</li>
          <li>Context preservation during model/mode switches</li>
          <li>Confirmation dialogs for potentially disruptive changes</li>
          <li>Real-time model availability checking</li>
          <li>Intelligent model categorization and filtering</li>
          <li>Quick switching to optimal models for each mode</li>
          <li>Visual indicators for current mode and model status</li>
        </ul>
      </div>
    </div>
  );
}

// Export the example for use in Storybook or documentation
export { ChatModeSelectorExample };