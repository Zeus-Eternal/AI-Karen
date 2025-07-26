/**
 * Extension Service - manages installed extensions (placeholder implementation)
 */

export interface ExtensionInfo {
  name: string;
  description: string;
  enabled: boolean;
}

class ExtensionService {
  private extensions: ExtensionInfo[] = [
    { name: 'Sample Extension', description: 'Example extension', enabled: true },
  ];

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
