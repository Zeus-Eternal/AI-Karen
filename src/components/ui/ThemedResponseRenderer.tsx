import React from 'react';
import { PluginThemeResolver } from '../../theme/PluginThemeResolver';
import { ThemedCard } from './ThemedCard';

interface ThemedResponseRendererProps {
  pluginName: string;
  response: any;
  resolver: PluginThemeResolver;
}

/**
 * Renders a plugin response inside a themed card. The resolver determines which
 * theme to apply based on plugin and response metadata.
 */
export const ThemedResponseRenderer: React.FC<ThemedResponseRendererProps> = ({
  pluginName,
  response,
  resolver,
}) => {
  const theme = resolver.resolve({
    pluginName,
    promptTheme: response?.metadata?.promptTheme,
    responseMetadata: response?.metadata,
  });

  if (!theme) {
    return <pre>{JSON.stringify(response, null, 2)}</pre>;
  }

  return (
    <ThemedCard theme={theme}>
      {/* Placeholder rendering logic. Real implementation would switch on theme.layout */}
      <pre>{JSON.stringify(response, null, 2)}</pre>
    </ThemedCard>
  );
};
