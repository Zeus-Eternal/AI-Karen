/**
 * Extension Service - manages installed extensions (placeholder implementation)
 */

export interface ExtensionInfo {
  name: string;
  description: string;
  enabled: boolean;
  health?: 'healthy' | 'degraded' | 'error';
  cpu?: number;
  memory?: number;
}

class ExtensionService {
  private extensions: ExtensionInfo[] = [
    { name: 'Sample Extension', description: 'Example extension', enabled: true, health: 'healthy', cpu: 5, memory: 100 },
  ];

  enableExtension(name: string): void {
    this.extensions = this.extensions.map(e => e.name === name ? { ...e, enabled: true } : e);
  }

  disableExtension(name: string): void {
    this.extensions = this.extensions.map(e => e.name === name ? { ...e, enabled: false } : e);
  }

  getExtensionStatus(name: string): 'healthy' | 'degraded' | 'error' | undefined {
    return this.extensions.find(e => e.name === name)?.health;
  }

  getExtensionResourceUsage(name: string): { cpu: number; memory: number } | undefined {
    const ext = this.extensions.find(e => e.name === name);
    return ext ? { cpu: ext.cpu || 0, memory: ext.memory || 0 } : undefined;
  }

  clearCache(): void {
    // Placeholder: nothing to clear
  }

  getCacheStats(): { size: number; keys: string[] } {
    return { size: this.extensions.length, keys: this.extensions.map(e => e.name) };
  }

  async getInstalledExtensions(): Promise<ExtensionInfo[]> {
    return this.extensions;
  }
}

let extensionService: ExtensionService | null = null;

export function getExtensionService(): ExtensionService {
  if (!extensionService) {
    extensionService = new ExtensionService();
  }
  return extensionService;
}

export function initializeExtensionService(): ExtensionService {
  extensionService = new ExtensionService();
  return extensionService;
}
