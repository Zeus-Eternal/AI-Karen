import { PluginStorePage } from '@/components/plugins';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Plugin Store | Karen AI',
  description: 'Discover and install plugins to enhance Karen AI capabilities',
};

export default function PluginsPage() {
  return <PluginStorePage />;
}
