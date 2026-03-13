import { describe, it, expect, beforeEach, vi } from 'vitest';
import ExtensionLifecycleService, {
  ExtensionLifecycleState,
  ExtensionLifecycleEventType,
  ExtensionLifecycleEvent
} from '../services/ExtensionLifecycleService';
import {
  CoPilotExtension,
  ExtensionCategory,
  ExtensionCapability,
  ExtensionConfig,
  ExtensionHealthStatus
} from '../types/extension';

// Mock extension
const createMockExtension = (id: string): CoPilotExtension => ({
  id,
  name: `Test Extension ${id}`,
  version: '1.0.0',
  description: `A test extension with ID ${id}`,
  author: 'Test Author',
  category: ExtensionCategory.CHAT,
  capabilities: [ExtensionCapability.CHAT_MODIFICATION],
  initialize: vi.fn().mockResolvedValue(undefined),
  execute: vi.fn().mockResolvedValue({
    id: 'test-response-id',
    status: 'success' as any,
    data: { result: 'success' }
  }),
  cleanup: vi.fn().mockResolvedValue(undefined),
  getStatus: vi.fn().mockReturnValue({
    enabled: true,
    initialized: true,
    health: ExtensionHealthStatus.HEALTHY,
    metrics: {
      requestCount: 0,
      successCount: 0,
      errorCount: 0,
      averageResponseTime: 0
    }
  })
});

describe('ExtensionLifecycleService', () => {
  let lifecycleService: ExtensionLifecycleService;
  
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    
    // Get a new instance for each test
    lifecycleService = ExtensionLifecycleService.getInstance();
    
    // Clear any registered extensions
    (lifecycleService as any).lifecycleStates.clear();
    (lifecycleService as any).lifecycleEventListeners.clear();
  });
  
  describe('getInstance', () => {
    it('should return a singleton instance', () => {
      const instance1 = ExtensionLifecycleService.getInstance();
      const instance2 = ExtensionLifecycleService.getInstance();
      
      expect(instance1).toBe(instance2);
    });
  });
  
  describe('loadExtension', () => {
    it('should load an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      const result = await lifecycleService.loadExtension(extension);
      
      expect(result).toBe(true);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.LOADED);
    });
    
    it('should fail to load an extension that is already loaded', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load once
      await lifecycleService.loadExtension(extension);
      
      // Try to load again
      const result = await lifecycleService.loadExtension(extension);
      
      expect(result).toBe(false);
    });
    
    it('should set lifecycle state to failed if loading fails', async () => {
      const extension = createMockExtension('test-extension');
      
      // Mock the extension service to fail registration
      const mockExtensionService = {
        registerExtension: vi.fn().mockResolvedValue(false)
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      const result = await lifecycleService.loadExtension(extension);
      
      expect(result).toBe(false);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.FAILED);
    });
  });
  
  describe('unloadExtension', () => {
    it('should unload an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Then unload
      const result = await lifecycleService.unloadExtension(extension.id);
      
      expect(result).toBe(true);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.NOT_LOADED);
    });
    
    it('should succeed if extension is not loaded', async () => {
      const result = await lifecycleService.unloadExtension('non-existent-extension');
      
      expect(result).toBe(true);
    });
    
    it('should set lifecycle state to failed if unloading fails', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Mock the extension service to fail unregistration
      const mockExtensionService = {
        unregisterExtension: vi.fn().mockResolvedValue(false)
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      const result = await lifecycleService.unloadExtension(extension.id);
      
      expect(result).toBe(false);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.FAILED);
    });
  });
  
  describe('enableExtension', () => {
    it('should enable an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Then enable
      const result = await lifecycleService.enableExtension(extension.id);
      
      expect(result).toBe(true);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.LOADED);
    });
    
    it('should set lifecycle state to failed if enabling fails', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Mock the extension service to fail enabling
      const mockExtensionService = {
        setExtensionEnabled: vi.fn().mockResolvedValue(false)
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      const result = await lifecycleService.enableExtension(extension.id);
      
      expect(result).toBe(false);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.FAILED);
    });
  });
  
  describe('disableExtension', () => {
    it('should disable an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Then disable
      const result = await lifecycleService.disableExtension(extension.id);
      
      expect(result).toBe(true);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.DISABLED);
    });
    
    it('should set lifecycle state to failed if disabling fails', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Mock the extension service to fail disabling
      const mockExtensionService = {
        setExtensionEnabled: vi.fn().mockResolvedValue(false)
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      const result = await lifecycleService.disableExtension(extension.id);
      
      expect(result).toBe(false);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.FAILED);
    });
  });
  
  describe('restartExtension', () => {
    it('should restart an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Then restart
      const result = await lifecycleService.restartExtension(extension.id);
      
      expect(result).toBe(true);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.LOADED);
    });
    
    it('should set lifecycle state to failed if restarting fails', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Mock the extension service to fail getting the extension
      const mockExtensionService = {
        getExtensionConfig: vi.fn().mockReturnValue({}),
        unregisterExtension: vi.fn().mockResolvedValue(true),
        getExtension: vi.fn().mockReturnValue(null)
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      const result = await lifecycleService.restartExtension(extension.id);
      
      expect(result).toBe(false);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.FAILED);
    });
  });
  
  describe('updateExtension', () => {
    it('should update an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      const newExtension = createMockExtension('test-extension');
      newExtension.version = '2.0.0';
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Then update
      const result = await lifecycleService.updateExtension(extension.id, newExtension);
      
      expect(result).toBe(true);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.LOADED);
    });
    
    it('should set lifecycle state to failed if updating fails', async () => {
      const extension = createMockExtension('test-extension');
      const newExtension = createMockExtension('test-extension');
      newExtension.version = '2.0.0';
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Mock the extension service to fail getting the extension
      const mockExtensionService = {
        getExtensionConfig: vi.fn().mockReturnValue({}),
        unregisterExtension: vi.fn().mockResolvedValue(true),
        getExtension: vi.fn().mockReturnValue(null)
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      const result = await lifecycleService.updateExtension(extension.id, newExtension);
      
      expect(result).toBe(false);
      expect(lifecycleService.getLifecycleState(extension.id)).toBe(ExtensionLifecycleState.FAILED);
    });
  });
  
  describe('getLifecycleState', () => {
    it('should return NOT_LOADED for an extension that has not been loaded', () => {
      const state = lifecycleService.getLifecycleState('non-existent-extension');
      
      expect(state).toBe(ExtensionLifecycleState.NOT_LOADED);
    });
    
    it('should return the correct state for a loaded extension', async () => {
      const extension = createMockExtension('test-extension');
      
      // Load first
      await lifecycleService.loadExtension(extension);
      
      // Then get state
      const state = lifecycleService.getLifecycleState(extension.id);
      
      expect(state).toBe(ExtensionLifecycleState.LOADED);
    });
  });
  
  describe('getAllLifecycleStates', () => {
    it('should return an empty map when no extensions have been loaded', () => {
      const states = lifecycleService.getAllLifecycleStates();
      
      expect(states.size).toBe(0);
    });
    
    it('should return all lifecycle states', async () => {
      const extension1 = createMockExtension('test-extension-1');
      const extension2 = createMockExtension('test-extension-2');
      
      // Load extensions
      await lifecycleService.loadExtension(extension1);
      await lifecycleService.loadExtension(extension2);
      
      // Get all states
      const states = lifecycleService.getAllLifecycleStates();
      
      expect(states.size).toBe(2);
      expect(states.get(extension1.id)).toBe(ExtensionLifecycleState.LOADED);
      expect(states.get(extension2.id)).toBe(ExtensionLifecycleState.LOADED);
    });
  });
  
  describe('event handling', () => {
    it('should emit and handle events correctly', async () => {
      const extension = createMockExtension('test-extension');
      const mockListener = vi.fn();
      
      // Register listener
      lifecycleService.addLifecycleEventListener(
        ExtensionLifecycleEventType.LOADED, 
        mockListener
      );
      
      // Load extension (which should emit an event)
      await lifecycleService.loadExtension(extension);
      
      // Check that listener was called
      expect(mockListener).toHaveBeenCalledWith({
        type: ExtensionLifecycleEventType.LOADED,
        extensionId: 'test-extension',
        timestamp: expect.any(Date),
        details: { version: '1.0.0' }
      });
    });
    
    it('should remove event listeners correctly', async () => {
      const extension = createMockExtension('test-extension');
      const mockListener = vi.fn();
      
      // Register listener
      lifecycleService.addLifecycleEventListener(
        ExtensionLifecycleEventType.LOADED, 
        mockListener
      );
      
      // Remove listener
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.LOADED, 
        mockListener
      );
      
      // Load extension (which should emit an event)
      await lifecycleService.loadExtension(extension);
      
      // Check that listener was not called
      expect(mockListener).not.toHaveBeenCalled();
    });
  });
  
  describe('performHealthCheck', () => {
    it('should return health status for all loaded extensions', async () => {
      const extension1 = createMockExtension('test-extension-1');
      const extension2 = createMockExtension('test-extension-2');
      
      // Load extensions
      await lifecycleService.loadExtension(extension1);
      await lifecycleService.loadExtension(extension2);
      
      // Mock the extension service to return status
      const mockExtensionService = {
        getExtensionStatus: vi.fn().mockReturnValue({
          health: ExtensionHealthStatus.HEALTHY,
          metrics: {
            errorCount: 0,
            successCount: 1
          }
        })
      };
      
      // Replace the extension service instance
      (lifecycleService as any).extensionService = mockExtensionService;
      
      // Perform health check
      const results = await lifecycleService.performHealthCheck();
      
      expect(results.size).toBe(2);
      expect(results.get(extension1.id)).toBe(ExtensionHealthStatus.HEALTHY);
      expect(results.get(extension2.id)).toBe(ExtensionHealthStatus.HEALTHY);
    });
    
    it('should skip health check for extensions that are not loaded', async () => {
      const extension = createMockExtension('test-extension');
      
      // Don't load the extension
      
      // Perform health check
      const results = await lifecycleService.performHealthCheck();
      
      expect(results.size).toBe(0);
    });
  });
});