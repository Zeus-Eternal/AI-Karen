/**
 * Extensions Service
 * Provides extension management functionality
 */

export interface ExtensionInfo {
  id?: string;
  name?: string;
  display_name?: string;
  description?: string;
  author?: string;
  version?: string;
  category?: string;
  tags?: string[];
  capabilities?: string[];
  rating?: number;
  downloads?: number;
  price?: string;
  license?: string;
  updated_at?: string;
  compatibility?: {
    kari_min_version?: string;
  };
  documentation_url?: string;
  verified?: boolean;
  installed?: boolean;
}

export interface ExtensionInstallRequest {
  extensionId: string;
}

export interface ExtensionUpdateRequest {
  extensionId: string;
}

export interface ExtensionResponse {
  success: boolean;
  message?: string;
  data?: unknown;
}

class ExtensionService {
  private baseUrl: string;

  constructor(baseUrl = '/api/extensions') {
    this.baseUrl = baseUrl;
  }

  async getInstalledExtensions(): Promise<ExtensionInfo[]> {
    try {
      const response = await fetch(`${this.baseUrl}/installed`);
      if (!response.ok) {
        throw new Error(`Failed to fetch installed extensions: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching installed extensions:', error);
      throw error;
    }
  }

  async getMarketplaceExtensions(): Promise<ExtensionInfo[]> {
    try {
      const response = await fetch(`${this.baseUrl}/marketplace`);
      if (!response.ok) {
        throw new Error(`Failed to fetch marketplace extensions: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching marketplace extensions:', error);
      throw error;
    }
  }

  async installExtension(request: ExtensionInstallRequest): Promise<ExtensionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/install`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        throw new Error(`Failed to install extension: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error installing extension:', error);
      throw error;
    }
  }

  async updateExtension(request: ExtensionUpdateRequest): Promise<ExtensionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        throw new Error(`Failed to update extension: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating extension:', error);
      throw error;
    }
  }

  async uninstallExtension(extensionId: string): Promise<ExtensionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/uninstall`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ extensionId }),
      });
      if (!response.ok) {
        throw new Error(`Failed to uninstall extension: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error uninstalling extension:', error);
      throw error;
    }
  }

  async loadExtension(name: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/load`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(`Failed to load extension: ${response.statusText}`);
      }
      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error loading extension:', error);
      throw error;
    }
  }

  async unloadExtension(name: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/unload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        throw new Error(`Failed to unload extension: ${response.statusText}`);
      }
      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error unloading extension:', error);
      throw error;
    }
  }
}

// Singleton instance
export const extensionService = new ExtensionService();
export default extensionService;
