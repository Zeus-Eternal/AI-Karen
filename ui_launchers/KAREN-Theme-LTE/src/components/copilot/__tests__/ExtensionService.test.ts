import { describe, it, expect, beforeEach, vi } from 'vitest';
import ExtensionService from '../services/ExtensionService';
import {
  CoPilotExtension,
  ExtensionCategory,
  ExtensionCapability,
  ExtensionContext,
  ExtensionConfig,
  ExtensionRequest,
  ExtensionRequestType,
  ExtensionResponse,
  ExtensionResponseStatus,
  ExtensionError,
  ExtensionErrorCode,
  ExtensionUIComponent,
  ExtensionUIComponentType,
  ExtensionUIComponentPosition,
  ExtensionHook,
  ExtensionContextProvider
} from '../types/extension';

// Mock logger
const mockLogger = {
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn()
};

// Mock context
const mockContext: ExtensionContext = {
  agentService: {},
  uiService: {},
  themeService: {},
  memoryService: {},
  conversationService: {},
  taskService: {},
  voiceService: {},
  config: {
    settings: {},
    global: {},
    userPreferences: {},
    tenant: {}
  },
  logger: mockLogger
};

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
    status: ExtensionResponseStatus.SUCCESS,
    data: { result: 'success' }
  }),
  cleanup: vi.fn().mockResolvedValue(undefined),
  getStatus: vi.fn().mockReturnValue({
    enabled: true,
    initialized: true,
    health: 'healthy' as any,
    metrics: {
      requestCount: 0,
      successCount: 0,
      errorCount: 0,
      averageResponseTime: 0
    }
  })
});

describe('ExtensionService', () => {
  let extensionService: ExtensionService;
  
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    
    // Get a new instance for each test
    extensionService = ExtensionService.getInstance();
    
    // Clear any registered extensions
    (extensionService as any).extensions.clear();
    (extensionService as any).configs.clear();
    (extensionService as any).enabledExtensions.clear();
    (extensionService as any).eventListeners.clear();
    (extensionService as any).uiComponents.clear();
    (extensionService as any).hooks.clear();
    (extensionService as any).contextProviders.clear();
  });
  
  describe('getInstance', () => {
    it('should return a singleton instance', () => {
      const instance1 = ExtensionService.getInstance();
      const instance2 = ExtensionService.getInstance();
      
      expect(instance1).toBe(instance2);
    });
  });
  
  describe('registerExtension', () => {
    it('should register an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      const result = await extensionService.registerExtension(extension);
      
      expect(result).toBe(true);
      expect(extension.initialize).toHaveBeenCalledWith(mockContext);
    });
    
    it('should fail to register an extension with duplicate ID', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register once
      await extensionService.registerExtension(extension);
      
      // Try to register again
      const result = await extensionService.registerExtension(extension);
      
      expect(result).toBe(false);
    });
    
    it('should fail to register an extension if initialization fails', async () => {
      const extension = createMockExtension('test-extension');
      extension.initialize = vi.fn().mockRejectedValue(new Error('Initialization failed'));
      
      const result = await extensionService.registerExtension(extension);
      
      expect(result).toBe(false);
    });
  });
  
  describe('unregisterExtension', () => {
    it('should unregister an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then unregister
      const result = await extensionService.unregisterExtension(extension.id);
      
      expect(result).toBe(true);
      expect(extension.cleanup).toHaveBeenCalled();
    });
    
    it('should fail to unregister an extension that is not registered', async () => {
      const result = await extensionService.unregisterExtension('non-existent-extension');
      
      expect(result).toBe(false);
    });
  });
  
  describe('getExtension', () => {
    it('should return a registered extension', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then get
      const result = extensionService.getExtension(extension.id);
      
      expect(result).toBe(extension);
    });
    
    it('should return undefined for an unregistered extension', () => {
      const result = extensionService.getExtension('non-existent-extension');
      
      expect(result).toBeUndefined();
    });
  });
  
  describe('getExtensions', () => {
    it('should return all registered extensions', async () => {
      const extension1 = createMockExtension('test-extension-1');
      const extension2 = createMockExtension('test-extension-2');
      
      // Register extensions
      await extensionService.registerExtension(extension1);
      await extensionService.registerExtension(extension2);
      
      // Get all
      const result = extensionService.getExtensions();
      
      expect(result).toContain(extension1);
      expect(result).toContain(extension2);
      expect(result).toHaveLength(2);
    });
    
    it('should return an empty array when no extensions are registered', () => {
      const result = extensionService.getExtensions();
      
      expect(result).toEqual([]);
    });
  });
  
  describe('executeExtensionRequest', () => {
    it('should execute an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      const request: Omit<ExtensionRequest, 'id'> = {
        type: ExtensionRequestType.EXECUTE,
        payload: { data: 'test' },
        metadata: {},
        userContext: {
          userId: 'test-user',
          roles: [],
          permissions: [],
          preferences: {}
        },
        sessionContext: {
          sessionId: 'test-session'
        }
      };
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then execute
      const result = await extensionService.executeExtensionRequest(extension.id, request);
      
      expect(result.status).toBe(ExtensionResponseStatus.SUCCESS);
      expect(extension.execute).toHaveBeenCalledWith(expect.objectContaining({
        type: ExtensionRequestType.EXECUTE,
        payload: { data: 'test' }
      }));
    });
    
    it('should fail to execute an extension that is not registered', async () => {
      const request: Omit<ExtensionRequest, 'id'> = {
        type: ExtensionRequestType.EXECUTE,
        payload: { data: 'test' },
        metadata: {},
        userContext: {
          userId: 'test-user',
          roles: [],
          permissions: [],
          preferences: {}
        },
        sessionContext: {
          sessionId: 'test-session'
        }
      };
      
      const result = await extensionService.executeExtensionRequest('non-existent-extension', request);
      
      expect(result.status).toBe(ExtensionResponseStatus.ERROR);
      expect(result.error?.code).toBe(ExtensionErrorCode.NOT_FOUND);
    });
    
    it('should fail to execute an extension that is not enabled', async () => {
      const extension = createMockExtension('test-extension');
      const request: Omit<ExtensionRequest, 'id'> = {
        type: ExtensionRequestType.EXECUTE,
        payload: { data: 'test' },
        metadata: {},
        userContext: {
          userId: 'test-user',
          roles: [],
          permissions: [],
          preferences: {}
        },
        sessionContext: {
          sessionId: 'test-session'
        }
      };
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Disable extension
      await extensionService.setExtensionEnabled(extension.id, false);
      
      // Then execute
      const result = await extensionService.executeExtensionRequest(extension.id, request);
      
      expect(result.status).toBe(ExtensionResponseStatus.ERROR);
      expect(result.error?.code).toBe(ExtensionErrorCode.GENERAL_ERROR);
    });
  });
  
  describe('setExtensionEnabled', () => {
    it('should enable an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then enable
      const result = await extensionService.setExtensionEnabled(extension.id, true);
      
      expect(result).toBe(true);
    });
    
    it('should disable an extension successfully', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then disable
      const result = await extensionService.setExtensionEnabled(extension.id, false);
      
      expect(result).toBe(true);
    });
    
    it('should fail to enable an extension that is not registered', async () => {
      const result = await extensionService.setExtensionEnabled('non-existent-extension', true);
      
      expect(result).toBe(false);
    });
  });
  
  describe('getExtensionStatus', () => {
    it('should return true for an enabled extension', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then check
      const result = extensionService.getExtensionStatus(extension.id);
      
      expect(result?.enabled).toBe(true);
    });
    
    it('should return false for a disabled extension', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Disable
      await extensionService.setExtensionEnabled(extension.id, false);
      
      // Then check
      const result = extensionService.getExtensionStatus(extension.id);
      
      expect(result?.enabled).toBe(false);
    });
    
    it('should return undefined for an unregistered extension', () => {
      const result = extensionService.getExtensionStatus('non-existent-extension');
      
      expect(result).toBeUndefined();
    });
  });
  
  describe('getExtensionConfig', () => {
    it('should return the config for a registered extension', async () => {
      const extension = createMockExtension('test-extension');
      const config: Partial<ExtensionConfig> = {
        settings: { testSetting: 'testValue' }
      };
      
      // Register with config
      await extensionService.registerExtension(extension, config);
      
      // Then get config
      const result = extensionService.getExtensionConfig(extension.id);
      
      expect(result).toEqual({
        settings: { testSetting: 'testValue' },
        global: {},
        userPreferences: {},
        tenant: {}
      });
    });
    
    it('should return undefined for an unregistered extension', () => {
      const result = extensionService.getExtensionConfig('non-existent-extension');
      
      expect(result).toBeUndefined();
    });
  });
  
  describe('updateExtensionConfig', () => {
    it('should update the config for a registered extension', async () => {
      const extension = createMockExtension('test-extension');
      const initialConfig: Partial<ExtensionConfig> = {
        settings: { testSetting: 'testValue' }
      };
      
      // Register with config
      await extensionService.registerExtension(extension, initialConfig);
      
      // Update config
      const updateConfig: Partial<ExtensionConfig> = {
        settings: { testSetting: 'updatedValue' }
      };
      const result = extensionService.updateExtensionConfig(extension.id, updateConfig);
      
      expect(result).toBe(true);
      
      // Check updated config
      const updatedConfig = extensionService.getExtensionConfig(extension.id);
      expect(updatedConfig?.settings.testSetting).toBe('updatedValue');
    });
    
    it('should fail to update the config for an unregistered extension', () => {
      const updateConfig: Partial<ExtensionConfig> = {
        settings: { testSetting: 'updatedValue' }
      };
      const result = extensionService.updateExtensionConfig('non-existent-extension', updateConfig);
      
      expect(result).toBe(false);
    });
  });
  
  describe('getExtensionStatus', () => {
    it('should return the status for a registered extension', async () => {
      const extension = createMockExtension('test-extension');
      
      // Register first
      await extensionService.registerExtension(extension);
      
      // Then get status
      const result = extensionService.getExtensionStatus(extension.id);
      
      expect(result).toEqual({
        enabled: true,
        initialized: true,
        health: 'healthy',
        metrics: {
          requestCount: 0,
          successCount: 0,
          errorCount: 0,
          averageResponseTime: 0
        }
      });
    });
    
    it('should return undefined for an unregistered extension', () => {
      const result = extensionService.getExtensionStatus('non-existent-extension');
      
      expect(result).toBeUndefined();
    });
  });
  
  describe('registerUIComponent', () => {
    it('should register a UI component successfully', async () => {
      const extension = createMockExtension('test-extension');
      const component: ExtensionUIComponent = {
        id: 'test-component',
        type: ExtensionUIComponentType.BUTTON,
        props: { label: 'Test Button' },
        position: ExtensionUIComponentPosition.TOOLBAR,
        visible: true,
        order: 1
      };
      
      // Register extension first
      await extensionService.registerExtension(extension);
      
      // Then register component
      const result = extensionService.registerUIComponent(extension.id, component);
      
      expect(result).toBe(true);
    });
    
    it('should fail to register a UI component for an unregistered extension', () => {
      const component: ExtensionUIComponent = {
        id: 'test-component',
        type: ExtensionUIComponentType.BUTTON,
        props: { label: 'Test Button' },
        position: ExtensionUIComponentPosition.TOOLBAR,
        visible: true,
        order: 1
      };
      
      const result = extensionService.registerUIComponent('non-existent-extension', component);
      
      expect(result).toBe(false);
    });
  });
  
  describe('getUIComponents', () => {
    it('should get UI components successfully', async () => {
      const extension = createMockExtension('test-extension');
      const component: ExtensionUIComponent = {
        id: 'test-component',
        type: ExtensionUIComponentType.BUTTON,
        props: { label: 'Test Button' },
        position: ExtensionUIComponentPosition.TOOLBAR,
        visible: true,
        order: 1
      };
      
      // Register extension first
      await extensionService.registerExtension(extension);
      
      // Register component
      extensionService.registerUIComponent(extension.id, component);
      
      // Then get components
      const result = extensionService.getUIComponents(extension.id);
      
      expect(result).toContain(component);
      expect(result).toHaveLength(1);
    });
    
    it('should return empty array for an unregistered extension', () => {
      const result = extensionService.getUIComponents('non-existent-extension');
      
      expect(result).toEqual([]);
    });
  });
  
  describe('event handling', () => {
    it('should emit and handle events correctly', async () => {
      const extension = createMockExtension('test-extension');
      const mockListener = vi.fn();
      
      // Register listener
      extensionService.addEventListener('extension_registered', mockListener);
      
      // Register extension (which should emit an event)
      await extensionService.registerExtension(extension);
      
      // Check that listener was called
      expect(mockListener).toHaveBeenCalledWith({
        type: 'extension_registered',
        extensionId: 'test-extension',
        timestamp: expect.any(Date)
      });
    });
  });
});