import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ChatBubble } from '@/components/chat';

describe('ChatBubble', () => {
  it('renders user message aligned to the right without meta bar', () => {
    const { container } = render(<ChatBubble role="user" content="Hi" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('flex-row-reverse');
    expect(screen.queryByText(/Model:/)).toBeNull();
  });

  it('renders assistant message with meta badges', () => {
    const { container } = render(
      <ChatBubble role="assistant" content="Hello" meta={{ model: 'gpt-4', latencyMs: 42 }} />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).not.toHaveClass('flex-row-reverse');
    expect(screen.getByText('Model: gpt-4')).toBeInTheDocument();
    expect(screen.getByText('Latency: 42ms')).toBeInTheDocument();
  });
});
