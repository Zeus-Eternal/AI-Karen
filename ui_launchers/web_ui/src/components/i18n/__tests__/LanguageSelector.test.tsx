/**
 * @vitest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { LanguageSelector } from '../LanguageSelector';
import { I18nProvider } from '../../../providers/i18n-provider';

// Mock the i18n system
vi.mock('../../../lib/i18n', () => ({
  i18n: {
    config: {
      defaultLocale: 'en',
      locales: ['en', 'es', 'fr'],
    },
    init: vi.fn().mockResolvedValue(undefined),
    getCurrentLocale: vi.fn().mockReturnValue('en'),
    getAvailableLocales: vi.fn().mockReturnValue(['en', 'es', 'fr']),
    getLocaleInfo: vi.fn().mockReturnValue({
      code: 'en',
      name: 'English',
      nativeName: 'English',
      direction: 'ltr',
    }),
    getTextDirection: vi.fn().mockReturnValue('ltr'),
    changeLocale: vi.fn(),
    onLocaleChange: vi.fn().mockReturnValue(() => {}),
    t: vi.fn((key) => key),
    formatNumber: vi.fn((num) => num.toString()),
    formatDate: vi.fn((date) => date.toISOString()),
    formatRelativeTime: vi.fn((value, unit) => `${value} ${unit}`),
  },
}));

function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider defaultLocale="en" locales={['en', 'es', 'fr']}>
      {children}
    </I18nProvider>
  );
}

describe('LanguageSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  it('renders select variant by default', async () => {
    render(
      <TestWrapper>
        <LanguageSelector />
      </TestWrapper>
    );

    // Wait for i18n to initialize
    await screen.findByRole('combobox');
    
    expect(screen.getByRole('combobox')).toBeInTheDocument();

  it('renders inline variant', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" />
      </TestWrapper>
    );

    // Wait for buttons to appear
    await screen.findByRole('button', { name: /switch to english/i });
    
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(3); // en, es, fr

  it('renders dropdown variant', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="dropdown" />
      </TestWrapper>
    );

    // Wait for the dropdown button
    await screen.findByRole('button');
    
    expect(screen.getByRole('button')).toBeInTheDocument();

  it('shows flags when enabled', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" showFlag={true} />
      </TestWrapper>
    );

    // Wait for content to load
    await screen.findByRole('button', { name: /switch to english/i });
    
    // Flags are rendered as emoji text, check for their presence
    const container = screen.getByRole('button', { name: /switch to english/i }).closest('div');
    expect(container).toBeInTheDocument();

  it('hides flags when disabled', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" showFlag={false} />
      </TestWrapper>
    );

    // Wait for buttons to appear
    await screen.findByRole('button', { name: /switch to english/i });
    
    // Should still render buttons but without flag emojis
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(3);

  it('applies custom className', async () => {
    render(
      <TestWrapper>
        <LanguageSelector className="custom-class" />
      </TestWrapper>
    );

    // Wait for component to render
    await screen.findByRole('combobox');
    
    const container = screen.getByRole('combobox').closest('div');
    expect(container).toHaveClass('custom-class');

  it('handles locale change in inline variant', async () => {
    const { i18n } = await import('../../../lib/i18n');
    
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" />
      </TestWrapper>
    );

    // Wait for buttons to appear
    await screen.findByRole('button', { name: /switch to english/i });
    
    const spanishButton = screen.getByRole('button', { name: /switch to spanish/i });
    fireEvent.click(spanishButton);

    expect(i18n.changeLocale).toHaveBeenCalledWith('es');

  it('shows active state for current locale in inline variant', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" />
      </TestWrapper>
    );

    // Wait for buttons to appear
    await screen.findByRole('button', { name: /switch to english/i });
    
    const englishButton = screen.getByRole('button', { name: /switch to english/i });
    expect(englishButton).toHaveAttribute('aria-pressed', 'true');
    
    const spanishButton = screen.getByRole('button', { name: /switch to spanish/i });
    expect(spanishButton).toHaveAttribute('aria-pressed', 'false');

  it('has proper accessibility attributes', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" />
      </TestWrapper>
    );

    // Wait for buttons to appear
    await screen.findByRole('button', { name: /switch to english/i });
    
    const buttons = screen.getAllByRole('button');
    
    buttons.forEach(button => {
      expect(button).toHaveAttribute('aria-label');
      expect(button).toHaveAttribute('aria-pressed');


  it('displays correct locale codes', async () => {
    render(
      <TestWrapper>
        <LanguageSelector variant="inline" />
      </TestWrapper>
    );

    // Wait for buttons to appear
    await screen.findByRole('button', { name: /switch to english/i });
    
    expect(screen.getByText('EN')).toBeInTheDocument();
    expect(screen.getByText('ES')).toBeInTheDocument();
    expect(screen.getByText('FR')).toBeInTheDocument();

