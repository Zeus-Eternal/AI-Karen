import { useCallback } from 'react';
import { PluginManifest } from '../types/backend';
import { useCopilotContext } from './useCopilot';

/**
 * Hook for toggling plugin state
 */
export function useCopilotTogglePlugin() {
  const { togglePlugin } = useCopilotContext();

  const handleTogglePlugin = useCallback(async (plugin: PluginManifest, enabled: boolean) => {
    try {
      // Use the togglePlugin function from the context
      await togglePlugin(plugin, enabled);
      
      // Send request to backend to update plugin state
      // In a real implementation, this would make an API call
      console.log(`Toggling plugin ${plugin.name} to ${enabled ? 'enabled' : 'disabled'}`);

      // Return success
      return true;
    } catch (error) {
      console.error('Error toggling plugin:', error);
      return false;
    }
  }, [togglePlugin]);

  return handleTogglePlugin;
}