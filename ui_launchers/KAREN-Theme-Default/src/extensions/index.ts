export * from './types';
export { ExtensionProvider as ExtensionContextProvider, ExtensionContext } from './ExtensionContext';
export { useExtensionContext } from '../hooks/use-extension-context';

// Re-export utilities and constants for convenience
export * from '../lib/extensions/constants';
export * from '../lib/extensions/navigationUtils';
export * from '../lib/extensions/extensionUtils';
