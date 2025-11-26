import { useContext } from 'react';
import { ContextBridgeContext, ContextBridgeState } from './context-bridge-context';

/**
 * Hook for using the ContextBridge
 */
export const useContextBridge = (): ContextBridgeState => {
  const context = useContext(ContextBridgeContext);
  
  if (!context) {
    throw new Error('useContextBridge must be used within a ContextBridgeProvider');
  }
  
  return context;
};