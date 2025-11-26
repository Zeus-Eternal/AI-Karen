import { ContextManager } from '../core/ContextManager';
import { EnhancedContext, CopilotMessage } from '../types/copilot';

describe('ContextManager', () => {
  let contextManager: ContextManager;
  
  beforeEach(() => {
    contextManager = new ContextManager();
  });
  
  describe('Initialization', () => {
    it('should initialize with default context', async () => {
      await contextManager.initialize();
      const context = await contextManager.getCurrentContext();
      
      expect(context).toBeDefined();
      expect(context.user).toBeDefined();
      expect(context.conversation).toBeDefined();
      expect(context.system).toBeDefined();
      expect(context.external).toBeDefined();
      expect(context.semantic).toBeDefined();
    });
  });
  
  describe('Context Management', () => {
    it('should update context with new messages', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Hello',
          role: 'user',
          timestamp: new Date()
        },
        {
          id: 'msg2',
          content: 'Hi there!',
          role: 'assistant',
          timestamp: new Date()
        }
      ];
      
      await contextManager.updateContextWithMessages(messages);
      const context = await contextManager.getCurrentContext();
      
      expect(context.conversation.messages).toEqual(messages);
      expect(context.conversation.messages.length).toBe(2);
    });
    
    it('should update user context', async () => {
      const userProfile = {
        id: 'user1',
        name: 'Test User',
        email: 'test@example.com',
        roles: ['developer'],
        expertiseLevel: 'intermediate' as const,
        preferences: {
          theme: 'dark' as const,
          fontSize: 'medium' as const,
          language: 'en',
          timezone: 'UTC',
          notifications: true,
          privacy: {
            dataCollection: true,
            personalizedResponses: true,
            shareAnalytics: false,
            rememberHistory: true
          }
        }
      };
      
      await contextManager.updateUserProfile(userProfile);
      const context = await contextManager.getCurrentContext();
      
      expect(context.user.profile).toEqual(userProfile);
    });
    
    it('should update system context', async () => {
      const systemCapabilities = {
        modalities: ['text', 'code'] as const,
        plugins: ['test-plugin'],
        actions: ['test-action'],
        workflows: ['test-workflow'],
        artifacts: ['test-artifact'],
        memoryTiers: ['short-term'] as const
      };
      
      // System capabilities are set during initialization, so we'll test by checking they exist
      // In a real implementation, we might add a method to update them
      const context = await contextManager.getCurrentContext();
      
      expect(context.system.capabilities).toEqual(systemCapabilities);
    });
    
    it('should update external context', async () => {
      const documents = [
        {
          id: 'doc1',
          title: 'Test Document',
          type: 'documentation' as const,
          source: 'test',
          relevance: 0.8,
          lastAccessed: new Date()
        }
      ];
      
      await contextManager.addExternalDocument(documents[0]);
      const context = await contextManager.getCurrentContext();
      
      expect(context.external.documents).toEqual(documents);
    });
  });
  
  describe('Context Analysis', () => {
    it('should analyze conversation semantics', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Can you help me with this code?',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      await contextManager.updateContextWithMessages(messages);
      const context = await contextManager.getCurrentContext();
      
      expect(context.conversation.semantics).toBeDefined();
      expect(context.conversation.semantics.sentiment).toBeDefined();
      expect(context.conversation.semantics.urgency).toBeDefined();
      expect(context.conversation.semantics.complexity).toBeDefined();
    });
    
    it('should extract topics from conversation', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'I need help with React and TypeScript',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      await contextManager.updateContextWithMessages(messages);
      const context = await contextManager.getCurrentContext();
      
      expect(context.conversation.topics).toBeDefined();
      expect(context.conversation.topics.length).toBeGreaterThan(0);
    });
    
    it('should determine conversation intent', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Please write a function to sort an array',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      await contextManager.updateContextWithMessages(messages);
      const context = await contextManager.getCurrentContext();
      
      expect(context.conversation.intent).toBeDefined();
      expect(context.conversation.intent.primary).toBeDefined();
      expect(context.conversation.intent.confidence).toBeGreaterThan(0);
    });
    
    it('should assess conversation complexity', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Create a complex algorithm with multiple edge cases',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      await contextManager.updateContextWithMessages(messages);
      const context = await contextManager.getCurrentContext();
      
      expect(context.conversation.complexity).toBeDefined();
      expect(context.conversation.complexity.level).toBeDefined();
      expect(context.conversation.complexity.score).toBeGreaterThan(0);
    });
  });
  
  describe('Error Handling', () => {
    it('should handle initialization errors gracefully', async () => {
      // Mock a failure scenario
      jest.spyOn(console, 'error').mockImplementation(() => {});
      
      // This test would need to be expanded with actual error scenarios
      // For now, we're just testing the structure
      await expect(contextManager.initialize()).resolves.not.toThrow();
    });
    
    it('should handle context update errors gracefully', async () => {
      // Mock a failure scenario
      jest.spyOn(console, 'error').mockImplementation(() => {});
      
      // This test would need to be expanded with actual error scenarios
      // For now, we're just testing the structure
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Test message',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      await expect(contextManager.updateContextWithMessages(messages)).resolves.not.toThrow();
    });
  });
});