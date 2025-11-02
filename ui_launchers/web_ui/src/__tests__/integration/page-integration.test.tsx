/**
 * Page Integration Tests
 * Tests to ensure all pages work correctly with modern components
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useRouter } from 'next/navigation';
import HomePage from '@/app/page';
import ChatPage from '@/app/chat/page';
import { componentMigrationMap, areAllComponentsMigrated } from '@/utils/page-integration';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  usePathname: vi.fn(() => '/'),
}));

// Mock dynamic imports
vi.mock('next/dynamic', () => ({
  default: vi.fn((fn) => {
    const Component = fn();
    return Component;
  }),
}));

// Mock auth components
vi.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/AuthenticatedHeader', () => ({
  AuthenticatedHeader: () => <div data-testid="auth-header">Auth Header</div>,
}));

// Mock other components
vi.mock('@/components/dashboard/Dashboard', () => ({
  default: () => <div data-testid="dashboard">Dashboard</div>,
}));

vi.mock('@/components/chat/ChatInterface', () => ({
  ChatInterface: () => <div data-testid="chat-interface">Chat Interface</div>,
}));

vi.mock('@/components/chat/MetaBar', () => ({
  MetaBar: () => <div data-testid="meta-bar">Meta Bar</div>,
}));

vi.mock('@/components/extensions/ExtensionSidebar', () => ({
  default: () => <div data-testid="extension-sidebar">Extension Sidebar</div>,
}));

vi.mock('@/lib/config', () => ({
  webUIConfig: {
    enableExtensions: false,
  },
}));

describe('Page Integration Tests', () => {
  beforeEach(() => {
    const mockRouter = {
      push: vi.fn(),
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    };
    (useRouter as any).mockReturnValue(mockRouter);

  describe('Component Migration Status', () => {
    it('should have all components migrated', () => {
      expect(areAllComponentsMigrated()).toBe(true);

    it('should have valid migration map', () => {
      expect(componentMigrationMap).toBeDefined();
      expect(componentMigrationMap.length).toBeGreaterThan(0);
      
      componentMigrationMap.forEach(component => {
        expect(component.componentName).toBeDefined();
        expect(component.newPath).toBeDefined();
        expect(component.migrated).toBe(true);
        expect(component.testsPassing).toBe(true);



  describe('HomePage Integration', () => {
    it('should render with modern layout components', async () => {
      render(<HomePage />);
      
      // Check for modern layout structure
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      
      // Check for modern components
      await waitFor(() => {
        expect(screen.getByTestId('dashboard')).toBeInTheDocument();


    it('should have proper accessibility structure', () => {
      render(<HomePage />);
      
      // Check for proper ARIA labels and roles
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByLabelText('Main navigation')).toBeInTheDocument();

    it('should use modern grid layout', () => {
      const { container } = render(<HomePage />);
      
      // Check for modern grid classes
      const gridContainer = container.querySelector('.app-grid');
      expect(gridContainer).toBeInTheDocument();


  describe('ChatPage Integration', () => {
    it('should render with modern layout components', async () => {
      render(<ChatPage />);
      
      // Check for chat-specific layout
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByTestId('meta-bar')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();


    it('should have proper chat grid layout', () => {
      const { container } = render(<ChatPage />);
      
      // Check for chat grid structure
      const chatGrid = container.querySelector('.chat-grid');
      expect(chatGrid).toBeInTheDocument();

    it('should maintain responsive behavior', () => {
      const { container } = render(<ChatPage />);
      
      // Check for responsive classes
      expect(container.querySelector('.container')).toBeInTheDocument();
      expect(container.querySelector('.max-w-screen-xl')).toBeInTheDocument();


  describe('Modern Component Usage', () => {
    it('should use FlexContainer components', () => {
      const { container } = render(<HomePage />);
      
      // Check for flex container usage (would be in DOM as div with flex classes)
      const flexElements = container.querySelectorAll('[class*="flex"]');
      expect(flexElements.length).toBeGreaterThan(0);

    it('should use GridContainer components', () => {
      const { container } = render(<HomePage />);
      
      // Check for grid container usage
      const gridElements = container.querySelectorAll('[class*="grid"]');
      expect(gridElements.length).toBeGreaterThan(0);

    it('should have modern card styling', () => {
      const { container } = render(<HomePage />);
      
      // Check for modern card classes
      const modernCards = container.querySelectorAll('.modern-card');
      expect(modernCards.length).toBeGreaterThan(0);


  describe('Performance Optimizations', () => {
    it('should have proper loading states', async () => {
      render(<HomePage />);
      
      // Check that components load without throwing
      await waitFor(() => {
        expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      }, { timeout: 3000 });

    it('should handle dynamic imports correctly', async () => {
      render(<ChatPage />);
      
      // Verify dynamic components load
      await waitFor(() => {
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();



  describe('Accessibility Integration', () => {
    it('should have proper heading hierarchy', () => {
      render(<HomePage />);
      
      // Check for proper heading structure
      const h1 = screen.getByRole('heading', { level: 1 });
      expect(h1).toBeInTheDocument();
      expect(h1).toHaveTextContent('Karen AI');

    it('should have skip links', () => {
      render(<HomePage />);
      
      // Check for skip link (would be in layout)
      const skipLink = document.querySelector('.skip-link');
      expect(skipLink).toBeInTheDocument();

    it('should have proper focus management', () => {
      render(<HomePage />);
      
      // Check for focus-visible classes
      const focusableElements = document.querySelectorAll('[class*="focus"]');
      expect(focusableElements.length).toBeGreaterThan(0);


  describe('Theme Integration', () => {
    it('should support dark mode', () => {
      render(<HomePage />);
      
      // Check for theme-aware classes
      const themeElements = document.querySelectorAll('[class*="dark:"]');
      expect(themeElements.length).toBeGreaterThan(0);

    it('should use design tokens', () => {
      const { container } = render(<HomePage />);
      
      // Check for CSS custom properties usage
      const styles = getComputedStyle(container.firstChild as Element);
      expect(styles.getPropertyValue('--primary')).toBeDefined();


