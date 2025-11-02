
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ChatBubble } from '@/components/chat';
import { webUIConfig } from '@/lib/config';

describe('ChatBubble', () => {
  it('renders user message aligned to the right without meta bar', () => {
    const { container } = render(<ChatBubble role="user" content="Hi" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('flex-row-reverse');
    expect(screen.queryByText(/Model:/)).toBeNull();

  it('renders assistant message with meta badges', () => {
    const { container } = render(
      <ChatBubble role="assistant" content="Hello" meta={{ model: 'gpt-4', latencyMs: 42, tokens: 128, cost: 0.000123 }} />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).not.toHaveClass('flex-row-reverse');
    expect(screen.getByText('Model: gpt-4')).toBeInTheDocument();
    expect(screen.getByText('Latency: 42ms')).toBeInTheDocument();
    expect(screen.getByText('Tokens: 128')).toBeInTheDocument();
    // Cost formatted to 6 decimals if toFixed exists
    expect(screen.getByText(/Cost: 0\.000123/)).toBeInTheDocument();

  it('omits meta bar when all meta flags disabled', () => {
    webUIConfig.showModelBadge = false;
    webUIConfig.showLatencyBadge = false;
    webUIConfig.showConfidenceBadge = false;
    const { container } = render(
      <ChatBubble role="assistant" content="Hi" meta={{ model: 'gpt-4', latencyMs: 10, confidence: 0.5 }} />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).not.toHaveClass('flex-row-reverse');
    expect(screen.queryByText(/Model:/)).toBeNull();
    webUIConfig.showModelBadge = true;
    webUIConfig.showLatencyBadge = true;
    webUIConfig.showConfidenceBadge = true;

