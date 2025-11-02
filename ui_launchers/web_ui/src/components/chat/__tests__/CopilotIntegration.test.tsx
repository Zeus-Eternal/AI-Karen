
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import CopilotActions, { type ChatContext } from '../CopilotActions';
import CopilotArtifacts, { type CopilotArtifact } from '../CopilotArtifacts';
import EnhancedMessageBubble from '../EnhancedMessageBubble';

// Mock the hooks and components
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ user: { user_id: 'test-user' } })
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() })
}));

vi.mock('@/lib/config', () => ({
  webUIConfig: {
    showModelBadge: true,
    showLatencyBadge: true,
    showConfidenceBadge: true
  }
}));

describe('Copilot Integration Demo', () => {
  const mockContext: ChatContext = {
    selectedText: 'function calculateSum(a, b) { return a + b; }',
    language: 'javascript',
    recentMessages: [
      {
        role: 'user',
        content: 'Help me optimize this function',
        timestamp: new Date()
      }
    ],
    codeContext: {
      hasCode: true,
      language: 'javascript',
      errorCount: 0
    },
    conversationContext: {
      topic: 'code optimization',
      intent: 'help',
      complexity: 'medium'
    }
  };

  const mockArtifacts: CopilotArtifact[] = [
    {
      id: 'artifact-1',
      type: 'code',
      title: 'Optimized Function',
      description: 'Performance-optimized version of your function',
      content: `function calculateSum(a, b) {
  // Input validation for better error handling
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new Error('Both arguments must be numbers');
  }
  
  // Use bitwise operations for integer addition (faster for integers)
  if (Number.isInteger(a) && Number.isInteger(b)) {
    return (a | 0) + (b | 0);
  }
  
  return a + b;
}`,
      language: 'javascript',
      metadata: {
        confidence: 0.95,
        complexity: 'low',
        impact: 'medium',
        category: 'optimization',
        tags: ['javascript', 'performance', 'validation']
      },
      status: 'pending',
      timestamp: new Date()
    },
    {
      id: 'artifact-2',
      type: 'test',
      title: 'Unit Tests',
      description: 'Comprehensive test suite for the function',
      content: `describe('calculateSum', () => {
  test('should add two positive numbers', () => {
    expect(calculateSum(2, 3)).toBe(5);

  test('should add negative numbers', () => {
    expect(calculateSum(-2, -3)).toBe(-5);

  test('should handle decimal numbers', () => {
    expect(calculateSum(2.5, 3.7)).toBeCloseTo(6.2);

  test('should throw error for non-numeric inputs', () => {
    expect(() => calculateSum('2', 3)).toThrow('Both arguments must be numbers');

});`,
      language: 'javascript',
      metadata: {
        confidence: 0.9,
        complexity: 'low',
        impact: 'high',
        category: 'testing',
        tags: ['javascript', 'testing', 'jest']
      },
      status: 'pending',
      timestamp: new Date()
    }
  ];

  it('renders CopilotActions with context-aware suggestions', () => {
    const mockOnActionTriggered = vi.fn();
    
    render(
      <CopilotActions
        onActionTriggered={mockOnActionTriggered}
        context={mockContext}
      />
    );

    expect(screen.getByText('Copilot Actions')).toBeInTheDocument();

  it('renders CopilotArtifacts with code suggestions', () => {
    const mockHandlers = {
      onApprove: vi.fn(),
      onReject: vi.fn(),
      onApply: vi.fn()
    };
    
    render(
      <CopilotArtifacts
        artifacts={mockArtifacts}
        {...mockHandlers}
      />
    );

    expect(screen.getByText('2 Copilot Artifacts')).toBeInTheDocument();
    expect(screen.getByText('Optimized Function')).toBeInTheDocument();
    expect(screen.getByText('Unit Tests')).toBeInTheDocument();

  it('renders EnhancedMessageBubble with artifacts integration', () => {
    const mockHandlers = {
      onApprove: vi.fn(),
      onReject: vi.fn(),
      onApply: vi.fn(),
      onCopy: vi.fn(),
      onRegenerate: vi.fn()
    };
    
    render(
      <EnhancedMessageBubble
        role="assistant"
        content="I've analyzed your function and created an optimized version with comprehensive tests. Here are the improvements:

```javascript
function calculateSum(a, b) {
  // Input validation for better error handling
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new Error('Both arguments must be numbers');
  }
  
  return a + b;
}
```

The optimized version includes input validation and better error handling."
        type="code"
        language="javascript"
        artifacts={mockArtifacts}
        meta={{
          confidence: 0.95,
          latencyMs: 1200,
          model: 'gpt-4',
          sources: ['MDN JavaScript Documentation']
        }}
        {...mockHandlers}
      />
    );

    // Should render the message content
    expect(screen.getByText(/I've analyzed your function/)).toBeInTheDocument();
    
    // Should show artifacts tab when artifacts are present
    expect(screen.getByText('Artifacts (2)')).toBeInTheDocument();

  it('demonstrates the complete copilot workflow', () => {
    // This test demonstrates how all components work together
    const mockActionHandler = vi.fn();
    const mockArtifactHandlers = {
      onApprove: vi.fn(),
      onReject: vi.fn(),
      onApply: vi.fn()
    };
    
    const { container } = render(
      <div className="copilot-demo">
        {/* Chat input area with copilot actions */}
        <div className="chat-input-area">
          <CopilotActions
            onActionTriggered={mockActionHandler}
            context={mockContext}
          />
        </div>
        
        {/* Enhanced message with artifacts */}
        <div className="chat-messages">
          <EnhancedMessageBubble
            role="assistant"
            content="Here's your optimized code with tests:"
            type="code"
            language="javascript"
            artifacts={mockArtifacts}
            onApprove={mockArtifactHandlers.onApprove}
            onReject={mockArtifactHandlers.onReject}
            onApply={mockArtifactHandlers.onApply}
          />
        </div>
      </div>
    );

    // Verify the complete integration is rendered
    expect(container.querySelector('.copilot-demo')).toBeInTheDocument();
    expect(screen.getByText('Copilot Actions')).toBeInTheDocument();
    expect(screen.getByText('Here\'s your optimized code with tests:')).toBeInTheDocument();

