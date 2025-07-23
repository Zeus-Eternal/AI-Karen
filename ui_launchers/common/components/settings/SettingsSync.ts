// Shared Settings Synchronization Component
// Framework-agnostic settings sync across devices and sessions

import { KarenSettings, Theme } from '../../abstractions/types';
import { storageManager, eventEmitter, errorHandler } from '../../abstractions/utils';
import { STORAGE_KEYS } from '../../abstractions/config';

export interface SettingsSyncOptions {
  enableCloudSync?: boolean;
  enableCrossTabSync?: boolean;
  enableAutoBackup?: boolean;
  backupInterval?: number; // in minutes
  maxBackups?: number;
}

export interface SyncStatus {
  lastSync: Date | null;
  isOnline: boolean;
  hasPendingChanges: boolean;
  syncInProgress: boolean;
  lastError: string | null;
}

export interface SettingsBackup {
  id: string;
  timestamp: Date;
  settings: KarenSettings;
  version: string;
  deviceId: string;
}

export interface SettingsSyncCallbacks {
  onSyncStart?: () => void;
  onSyncComplete?: (success: boolean) => void;
  onSyncError?: (error: string) => void;
  onSettingsReceived?: (settings: KarenSettings) => void;
  onConflictDetected?: (localSettings: KarenSettings, remoteSettings: KarenSettings) => void;
}

export class SharedSettingsSync {
  private options: SettingsSyncOptions;
  private callbacks: SettingsSyncCallbacks;
  private theme: Theme;
  private syncStatus: SyncStatus;
  private backupTimer: NodeJS.Timeout | null = null;
  private deviceId: string;

  constructor(
    theme: Theme,
    options: SettingsSyncOptions = {},
    callbacks: SettingsSyncCallbacks = {}
  ) {
    this.theme = theme;
    this.options = {
      enableCloudSync: false, // Disabled by default for privacy
      enableCrossTabSync: true,
      enableAutoBackup: true,
      backupInterval: 30, // 30 minutes
      maxBackups: 10,
      ...options
    };
    this.callbacks = callbacks;

    this.syncStatus = {
      lastSync: null,
      isOnline: navigator.onLine,
      hasPendingChanges: false,
      syncInProgress: false,
      lastError: null
    };

    this.deviceId = this.getOrCreateDeviceId();

    this.setupEventListeners();
    this.startAutoBackup();
  }

  // Get current sync status
  getSyncStatus(): SyncStatus {
    return { ...this.syncStatus };
  }

  // Update sync status
  private updateSyncStatus(newStatus: Partial<SyncStatus>): void {
    this.syncStatus = { ...this.syncStatus, ...newStatus };
    eventEmitter.emit('settings-sync-status-changed', this.syncStatus);
  }

  // Sync settings to cloud (placeholder implementation)
  async syncToCloud(settings: KarenSettings): Promise<void> {
    if (!this.options.enableCloudSync) {
      throw new Error('Cloud sync is not enabled');
    }

    this.updateSyncStatus({ syncInProgress: true, lastError: null });

    if (this.callbacks.onSyncStart) {
      this.callbacks.onSyncStart();
    }

    try {
      // This would integrate with a real cloud service
      // For now, we'll simulate the sync process
      await this.simulateCloudSync(settings);

      this.updateSyncStatus({
        lastSync: new Date(),
        syncInProgress: false,
        hasPendingChanges: false
      });

      if (this.callbacks.onSyncComplete) {
        this.callbacks.onSyncComplete(true);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sync failed';
      this.updateSyncStatus({
        syncInProgress: false,
        lastError: errorMessage
      });

      if (this.callbacks.onSyncError) {
        this.callbacks.onSyncError(errorMessage);
      }

      if (this.callbacks.onSyncComplete) {
        this.callbacks.onSyncComplete(false);
      }

      throw error;
    }
  }

  // Sync settings from cloud (placeholder implementation)
  async syncFromCloud(): Promise<KarenSettings | null> {
    if (!this.options.enableCloudSync) {
      throw new Error('Cloud sync is not enabled');
    }

    this.updateSyncStatus({ syncInProgress: true, lastError: null });

    try {
      // This would integrate with a real cloud service
      const remoteSettings = await this.simulateCloudFetch();

      if (remoteSettings) {
        const localSettings = storageManager.get<KarenSettings>(STORAGE_KEYS.SETTINGS);
        
        if (localSettings && this.hasConflict(localSettings, remoteSettings)) {
          if (this.callbacks.onConflictDetected) {
            this.callbacks.onConflictDetected(localSettings, remoteSettings);
          }
          // Return remote settings but don't auto-apply
          return remoteSettings;
        }

        // Apply remote settings
        storageManager.set(STORAGE_KEYS.SETTINGS, remoteSettings);
        
        if (this.callbacks.onSettingsReceived) {
          this.callbacks.onSettingsReceived(remoteSettings);
        }
      }

      this.updateSyncStatus({
        lastSync: new Date(),
        syncInProgress: false
      });

      return remoteSettings;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Sync failed';
      this.updateSyncStatus({
        syncInProgress: false,
        lastError: errorMessage
      });

      if (this.callbacks.onSyncError) {
        this.callbacks.onSyncError(errorMessage);
      }

      throw error;
    }
  }

  // Enable cross-tab synchronization
  enableCrossTabSync(): void {
    if (!this.options.enableCrossTabSync) return;

    // Listen for storage changes from other tabs
    window.addEventListener('storage', (event) => {
      if (event.key === STORAGE_KEYS.SETTINGS && event.newValue) {
        try {
          const newSettings = JSON.parse(event.newValue) as KarenSettings;
          
          if (this.callbacks.onSettingsReceived) {
            this.callbacks.onSettingsReceived(newSettings);
          }

          eventEmitter.emit('settings-synced-from-tab', newSettings);
        } catch (error) {
          errorHandler.logError(error as Error, 'cross-tab sync');
        }
      }
    });
  }

  // Create a backup of current settings
  async createBackup(settings: KarenSettings): Promise<string> {
    const backup: SettingsBackup = {
      id: this.generateBackupId(),
      timestamp: new Date(),
      settings: { ...settings },
      version: '1.0',
      deviceId: this.deviceId
    };

    const backups = this.getBackups();
    backups.unshift(backup);

    // Limit number of backups
    if (this.options.maxBackups && backups.length > this.options.maxBackups) {
      backups.splice(this.options.maxBackups);
    }

    storageManager.set(`${STORAGE_KEYS.SETTINGS}-backups`, backups);
    
    eventEmitter.emit('settings-backup-created', backup);
    return backup.id;
  }

  // Restore settings from backup
  async restoreFromBackup(backupId: string): Promise<KarenSettings> {
    const backups = this.getBackups();
    const backup = backups.find(b => b.id === backupId);

    if (!backup) {
      throw new Error('Backup not found');
    }

    // Restore settings
    storageManager.set(STORAGE_KEYS.SETTINGS, backup.settings);
    
    if (this.callbacks.onSettingsReceived) {
      this.callbacks.onSettingsReceived(backup.settings);
    }

    eventEmitter.emit('settings-restored-from-backup', backup);
    return backup.settings;
  }

  // Get all available backups
  getBackups(): SettingsBackup[] {
    const backups = storageManager.get<SettingsBackup[]>(`${STORAGE_KEYS.SETTINGS}-backups`);
    return backups || [];
  }

  // Delete a backup
  deleteBackup(backupId: string): void {
    const backups = this.getBackups().filter(b => b.id !== backupId);
    storageManager.set(`${STORAGE_KEYS.SETTINGS}-backups`, backups);
    eventEmitter.emit('settings-backup-deleted', backupId);
  }

  // Clear all backups
  clearAllBackups(): void {
    storageManager.remove(`${STORAGE_KEYS.SETTINGS}-backups`);
    eventEmitter.emit('settings-backups-cleared');
  }

  // Export settings for manual backup
  exportSettings(settings: KarenSettings): string {
    const exportData = {
      exportDate: new Date().toISOString(),
      version: '1.0',
      deviceId: this.deviceId,
      settings
    };

    return JSON.stringify(exportData, null, 2);
  }

  // Import settings from manual backup
  async importSettings(importData: string): Promise<KarenSettings> {
    try {
      const parsed = JSON.parse(importData);
      
      if (!parsed.settings) {
        throw new Error('Invalid import data: missing settings');
      }

      const settings = parsed.settings as KarenSettings;
      
      // Create backup before importing
      const currentSettings = storageManager.get<KarenSettings>(STORAGE_KEYS.SETTINGS);
      if (currentSettings) {
        await this.createBackup(currentSettings);
      }

      // Import settings
      storageManager.set(STORAGE_KEYS.SETTINGS, settings);
      
      if (this.callbacks.onSettingsReceived) {
        this.callbacks.onSettingsReceived(settings);
      }

      eventEmitter.emit('settings-imported', settings);
      return settings;

    } catch (error) {
      throw new Error('Failed to import settings: ' + (error instanceof Error ? error.message : 'Unknown error'));
    }
  }

  // Mark settings as having pending changes
  markPendingChanges(): void {
    this.updateSyncStatus({ hasPendingChanges: true });
  }

  // Get sync statistics
  getSyncStats(): {
    totalBackups: number;
    lastBackup: Date | null;
    lastSync: Date | null;
    deviceId: string;
    isOnline: boolean;
  } {
    const backups = this.getBackups();
    const lastBackup = backups.length > 0 ? backups[0].timestamp : null;

    return {
      totalBackups: backups.length,
      lastBackup,
      lastSync: this.syncStatus.lastSync,
      deviceId: this.deviceId,
      isOnline: this.syncStatus.isOnline
    };
  }

  // Get render data
  getRenderData(): SettingsSyncRenderData {
    return {
      status: this.getSyncStatus(),
      options: this.options,
      stats: this.getSyncStats(),
      backups: this.getBackups(),
      theme: this.theme,
      handlers: {
        onSyncToCloud: (settings: KarenSettings) => this.syncToCloud(settings),
        onSyncFromCloud: () => this.syncFromCloud(),
        onCreateBackup: (settings: KarenSettings) => this.createBackup(settings),
        onRestoreBackup: (backupId: string) => this.restoreFromBackup(backupId),
        onDeleteBackup: (backupId: string) => this.deleteBackup(backupId),
        onClearBackups: () => this.clearAllBackups(),
        onExportSettings: (settings: KarenSettings) => this.exportSettings(settings),
        onImportSettings: (data: string) => this.importSettings(data)
      }
    };
  }

  // Private helper methods
  private setupEventListeners(): void {
    // Online/offline status
    window.addEventListener('online', () => {
      this.updateSyncStatus({ isOnline: true });
    });

    window.addEventListener('offline', () => {
      this.updateSyncStatus({ isOnline: false });
    });

    // Cross-tab sync
    if (this.options.enableCrossTabSync) {
      this.enableCrossTabSync();
    }
  }

  private startAutoBackup(): void {
    if (!this.options.enableAutoBackup || !this.options.backupInterval) return;

    this.backupTimer = setInterval(async () => {
      try {
        const settings = storageManager.get<KarenSettings>(STORAGE_KEYS.SETTINGS);
        if (settings) {
          await this.createBackup(settings);
        }
      } catch (error) {
        errorHandler.logError(error as Error, 'auto backup');
      }
    }, this.options.backupInterval * 60 * 1000); // Convert minutes to milliseconds
  }

  private getOrCreateDeviceId(): string {
    let deviceId = storageManager.get<string>('device-id');
    
    if (!deviceId) {
      deviceId = `device-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      storageManager.set('device-id', deviceId);
    }
    
    return deviceId;
  }

  private generateBackupId(): string {
    return `backup-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private hasConflict(local: KarenSettings, remote: KarenSettings): boolean {
    // Simple conflict detection - in a real implementation, this would be more sophisticated
    return JSON.stringify(local) !== JSON.stringify(remote);
  }

  private async simulateCloudSync(settings: KarenSettings): Promise<void> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Simulate potential failure
    if (Math.random() < 0.1) { // 10% failure rate
      throw new Error('Network error during sync');
    }
    
    // In a real implementation, this would send data to a cloud service
    console.log('Settings synced to cloud:', settings);
  }

  private async simulateCloudFetch(): Promise<KarenSettings | null> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Simulate no remote data
    if (Math.random() < 0.5) {
      return null;
    }
    
    // In a real implementation, this would fetch from a cloud service
    return storageManager.get<KarenSettings>(STORAGE_KEYS.SETTINGS);
  }

  // Cleanup
  destroy(): void {
    if (this.backupTimer) {
      clearInterval(this.backupTimer);
      this.backupTimer = null;
    }
  }
}

// Supporting interfaces
export interface SettingsSyncRenderData {
  status: SyncStatus;
  options: SettingsSyncOptions;
  stats: {
    totalBackups: number;
    lastBackup: Date | null;
    lastSync: Date | null;
    deviceId: string;
    isOnline: boolean;
  };
  backups: SettingsBackup[];
  theme: Theme;
  handlers: {
    onSyncToCloud: (settings: KarenSettings) => Promise<void>;
    onSyncFromCloud: () => Promise<KarenSettings | null>;
    onCreateBackup: (settings: KarenSettings) => Promise<string>;
    onRestoreBackup: (backupId: string) => Promise<KarenSettings>;
    onDeleteBackup: (backupId: string) => void;
    onClearBackups: () => void;
    onExportSettings: (settings: KarenSettings) => string;
    onImportSettings: (data: string) => Promise<KarenSettings>;
  };
}

// Utility functions
export function createSettingsSync(
  theme: Theme,
  options: SettingsSyncOptions = {},
  callbacks: SettingsSyncCallbacks = {}
): SharedSettingsSync {
  return new SharedSettingsSync(theme, options, callbacks);
}

export function formatSyncStatus(status: SyncStatus): string {
  if (status.syncInProgress) {
    return 'Syncing...';
  }
  
  if (status.lastError) {
    return `Error: ${status.lastError}`;
  }
  
  if (status.lastSync) {
    const timeDiff = Date.now() - status.lastSync.getTime();
    const minutes = Math.floor(timeDiff / 60000);
    
    if (minutes < 1) {
      return 'Synced just now';
    } else if (minutes < 60) {
      return `Synced ${minutes} minute${minutes === 1 ? '' : 's'} ago`;
    } else {
      const hours = Math.floor(minutes / 60);
      return `Synced ${hours} hour${hours === 1 ? '' : 's'} ago`;
    }
  }
  
  return 'Never synced';
}

export function validateImportData(data: string): { valid: boolean; error?: string } {
  try {
    const parsed = JSON.parse(data);
    
    if (!parsed.settings) {
      return { valid: false, error: 'Missing settings data' };
    }
    
    // Basic validation of settings structure
    const settings = parsed.settings;
    const requiredFields = ['memoryDepth', 'personalityTone', 'personalityVerbosity'];
    
    for (const field of requiredFields) {
      if (!(field in settings)) {
        return { valid: false, error: `Missing required field: ${field}` };
      }
    }
    
    return { valid: true };
    
  } catch (error) {
    return { valid: false, error: 'Invalid JSON format' };
  }
}