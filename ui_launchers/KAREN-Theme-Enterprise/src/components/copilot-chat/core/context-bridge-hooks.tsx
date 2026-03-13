import { useContext } from 'react';
import { ContextBridgeContext } from './context-bridge-context';

export const useContextBridge = () => {
  const context = useContext(ContextBridgeContext);
  if (!context) {
    throw new Error('useContextBridge must be used within a ContextBridgeProvider');
  }
  return context;
};

export const useViewId = () => {
  const context = useContextBridge();
  return context.viewId;
};

export const useInterfaceMode = () => {
  const context = useContextBridge();
  return context.interfaceMode;
};

export const useActivePanel = () => {
  const context = useContextBridge();
  return context.activePanel;
};

export const useInputModality = () => {
  const context = useContextBridge();
  return context.inputModality;
};

export const useClient = () => {
  const context = useContextBridge();
  return context.client;
};

export const useCapabilities = () => {
  const context = useContextBridge();
  return context.capabilities;
};

export const useIntentHints = () => {
  const context = useContextBridge();
  return context.intentHints;
};

export const usePluginHints = () => {
  const context = useContextBridge();
  return context.pluginHints;
};

export const useCreateBackendRequest = () => {
  const context = useContextBridge();
  return context.createBackendRequest;
};

export const useProcessBackendResponse = () => {
  const context = useContextBridge();
  return context.processBackendResponse;
};

export const useUpdateUIContext = () => {
  const context = useContextBridge();
  return context.updateUIContext;
};

export const useAddIntentHint = () => {
  const context = useContextBridge();
  return context.addIntentHint;
};

export const useAddPluginHint = () => {
  const context = useContextBridge();
  return context.addPluginHint;
};

export const useClearHints = () => {
  const context = useContextBridge();
  return context.clearHints;
};