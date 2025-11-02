import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { ExtensionProvider } from '@/extensions/ExtensionContext';
import { useExtensionNavigation } from '../useExtensionNavigation';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ExtensionProvider>{children}</ExtensionProvider>
);

describe('useExtensionNavigation', () => {
  it('returns default navigation state', () => {
    const { result } = renderHook(() => useExtensionNavigation(), { wrapper });
    expect(result.current.navigation.currentCategory).toBe('Plugins');
    expect(result.current.navigation.currentLevel).toBe('category');

  it('can switch category', () => {
    const { result } = renderHook(() => useExtensionNavigation(), { wrapper });
    act(() => {
      result.current.setCategory('Extensions');

    expect(result.current.navigation.currentCategory).toBe('Extensions');

  it('can go back after breadcrumb push', () => {
    const { result } = renderHook(() => useExtensionNavigation(), { wrapper });
    act(() => {
      result.current.pushBreadcrumb({ level: 'submenu', name: 'LLM', id: 'llm' });

    expect(result.current.navigation.currentLevel).toBe('submenu');
    act(() => {
      result.current.goBack();

    expect(result.current.navigation.currentLevel).toBe('category');

