import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MetaBar } from '@/components/chat';

describe('MetaBar', () => {
  it('renders provided metadata badges', () => {
    render(<MetaBar model="gpt-4" latencyMs={123} confidence={0.9} annotations={2} />);

    expect(screen.getByText('Model: gpt-4')).toBeInTheDocument();
    expect(screen.getByText('Latency: 123ms')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 0.9')).toBeInTheDocument();
    expect(screen.getByText('Annotations: 2')).toBeInTheDocument();
  });

  it('hides badges for absent fields', () => {
    render(<MetaBar model="gpt-4" />);

    expect(screen.getByText('Model: gpt-4')).toBeInTheDocument();
    expect(screen.queryByText(/Latency:/)).toBeNull();
    expect(screen.queryByText(/Confidence:/)).toBeNull();
    expect(screen.queryByText(/Annotations:/)).toBeNull();
  });
});
