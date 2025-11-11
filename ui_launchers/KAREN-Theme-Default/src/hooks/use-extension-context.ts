"use client";

import { useContext } from 'react';
import { ExtensionContext } from '@/extensions/ExtensionContext';

export const useExtensionContext = () => {
  const context = useContext(ExtensionContext);
  if (context === undefined) {
    throw new Error('useExtensionContext must be used within an ExtensionProvider');
  }
  return context;
};