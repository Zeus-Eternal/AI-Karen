import type { ExtensionCacheConfig } from './types';

let cacheConfig: ExtensionCacheConfig | null = null;

export function setCacheConfig(config: ExtensionCacheConfig) {
  cacheConfig = config;
}

export function getCacheConfig(): ExtensionCacheConfig | null {
  return cacheConfig;
}
