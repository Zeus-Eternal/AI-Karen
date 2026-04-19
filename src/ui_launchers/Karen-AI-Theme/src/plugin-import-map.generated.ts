/**
 * Generated plugin import map (frontend).
 *
 * Single loading authority: `plugin_host/loader.ts` must import from here and
 * resolve ONLY installed UI packages under `src/plugin_repo/<plugin-id>/`.
 */
import type React from 'react';

export type PluginImporter = () => Promise<{
  default: React.ComponentType<Record<string, unknown>>;
}>;

export type PluginImportMap = Record<string, PluginImporter>;

export const PLUGIN_IMPORT_MAP: PluginImportMap = {
  "weather-query": () => import("@/plugin_repo/weather-query/weather-query"),
  "time-query": () => import("@/plugin_repo/time-query/ui/DateTimePluginPage"),
};
