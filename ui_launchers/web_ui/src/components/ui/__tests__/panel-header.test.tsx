
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PanelHeader } from '../panel-header';

describe('PanelHeader', () => {
  it('renders close button when showCloseButton is true and onClose is provided', () => {
    const onClose = vi.fn();
    
    render(
      <PanelHeader
        title="Test Title"
        showCloseButton={true}
        onClose={onClose}
      />
    );
    
    expect(screen.getByRole('button', { name: /close panel/i })).toBeInTheDocument();

  it('does not render close button when showCloseButton is false', () => {
    const onClose = vi.fn();
    
    render(
      <PanelHeader
        title="Test Title"
        showCloseButton={false}
        onClose={onClose}
      />
    );
    
    expect(screen.queryByRole('button', { name: /close panel/i })).not.toBeInTheDocument();

  it('does not render close button when onClose is not provided', () => {
    render(
      <PanelHeader
        title="Test Title"
        showCloseButton={true}
      />
    );
    
    expect(screen.queryByRole('button', { name: /close panel/i })).not.toBeInTheDocument();

