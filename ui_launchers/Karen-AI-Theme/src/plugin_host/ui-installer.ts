/**
 * UI Installer Service - Handles frontend UI installation lifecycle for plugins.
 * 
 * This service manages:
 * - Installing plugin UI from backend materialization
 * - Removing plugin UI from frontend
 * - Restoring plugin UI from source
 * - Tracking installation state
 * 
 * Works with the backend UI materialization pipeline to coordinate
 * frontend UI installation lifecycle.
 */



/**
 * Frontend UI installation status
 */
export type UIInstallStatus = 
  | 'not_installed'    // UI not installed in frontend
  | 'installing'       // UI installation in progress
  | 'installed'        // UI installed and ready for registration
  | 'removing'         // UI removal in progress
  | 'restoring'        // UI restoration in progress
  | 'error';           // Installation/error state

/**
 * UI installation result
 */
export interface UIInstallResult {
  success: boolean;
  message?: string;
  pluginId: string;
  status: UIInstallStatus;
}

/**
 * UI Installer Service
 */
export class UIInstallerService {
  private static instance: UIInstallerService;
  private apiBase = '/api/ui-materialization';
  private storageKey = 'karen-ui-installations';

  private constructor() {}

  /**
   * Get singleton instance
   */
  public static getInstance(): UIInstallerService {
    if (!UIInstallerService.instance) {
      UIInstallerService.instance = new UIInstallerService();
    }
    return UIInstallerService.instance;
  }

  /**
   * Load installation state from localStorage
   */
  private loadInstallations(): Record<string, UIInstallStatus> {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : {};
    } catch (error) {
      console.error('Failed to load UI installations from localStorage:', error);
      return {};
    }
  }

  /**
   * Save installation state to localStorage
   */
  private saveInstallations(installations: Record<string, UIInstallStatus>): void {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(installations));
    } catch (error) {
      console.error('Failed to save UI installations to localStorage:', error);
    }
  }

  /**
   * Install UI for a plugin
   * @param pluginId The plugin ID to install UI for
   * @returns Installation result
   */
  public async installUI(pluginId: string): Promise<UIInstallResult> {
    try {
      // Special handling for weather-query since it's manually installed
      if (pluginId === 'weather-query') {
        // Save installation state
        const installations = this.loadInstallations();
        installations[pluginId] = 'installed';
        this.saveInstallations(installations);

        return {
          success: true,
          message: 'UI is already installed (manually installed)',
          pluginId,
          status: 'installed',
        };
      }

      // Call backend to materialize UI artifacts for this plugin
      const response = await fetch(`${this.apiBase}/materialize/${pluginId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        return {
          success: false,
          message: errorData.detail || 'Failed to install UI',
          pluginId,
          status: 'error',
        };
      }

      // Save successful installation state
      const installations = this.loadInstallations();
      installations[pluginId] = 'installed';
      this.saveInstallations(installations);

      return {
        success: true,
        message: 'UI installed successfully',
        pluginId,
        status: 'installed',
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        pluginId,
        status: 'error',
      };
    }
  }

  /**
   * Remove UI for a plugin
   * @param pluginId The plugin ID to remove UI for
   * @returns Removal result
   */
  public async removeUI(pluginId: string): Promise<UIInstallResult> {
    try {
      // Clear stored installation state
      const installations = this.loadInstallations();
      delete installations[pluginId];
      this.saveInstallations(installations);

      // Call backend to clean up UI artifacts for this plugin
      // Note: We'll use the cleanup endpoint with specific plugin targeting
      // For now, we'll trigger general cleanup and rely on backend to remove specific plugin
      const response = await fetch(`${this.apiBase}/cleanup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        return {
          success: false,
          message: errorData.detail || 'Failed to remove UI',
          pluginId,
          status: 'error',
        };
      }

      return {
        success: true,
        message: 'UI removed successfully',
        pluginId,
        status: 'not_installed',
      };
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        pluginId,
        status: 'error',
      };
    }
  }

  /**
   * Restore UI for a plugin from source
   * @param pluginId The plugin ID to restore UI for
   * @returns Restoration result
   */
  public async restoreUI(pluginId: string): Promise<UIInstallResult> {
    try {
      // Restoration is essentially re-installing from source
      return await this.installUI(pluginId);
    } catch (error) {
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        pluginId,
        status: 'error',
      };
    }
  }

  /**
   * Get UI installation status for a plugin
   * @param pluginId The plugin ID to check
   * @returns UI installation status
   */
  public async getUIInstallStatus(pluginId: string): Promise<UIInstallStatus> {
    // First check localStorage for persisted state
    const installations = this.loadInstallations();
    if (installations[pluginId]) {
      return installations[pluginId];
    }

    try {
      const response = await fetch(`${this.apiBase}/plugin/${pluginId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        // If plugin not found or no UI capabilities, UI is not installed
        if (response.status === 404) {
          return 'not_installed';
        }
        throw new Error(`Failed to get UI status: ${response.status}`);
      }

      // If we get UI data back, the UI is installable/available
      // In a more sophisticated implementation, we'd check if it's actually installed
      // For now, we'll assume if the backend says it has UI capability, it's installable
      return 'not_installed'; // Default to not installed, actual state would be tracked elsewhere
    } catch (error) {
      console.error(`Error checking UI install status for ${pluginId}:`, error);
      return 'not_installed';
    }
  }

  /**
   * Get the import map for frontend plugin loading
   * @returns Import map for plugin components
   */
  public async getImportMap(): Promise<Record<string, string>> {
    try {
      const response = await fetch(`${this.apiBase}/import-map`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get import map');
      }

      const data = await response.json();
      return data.data.import_map;
    } catch (error) {
      console.error('Error getting import map:', error);
      return {};
    }
  }
}