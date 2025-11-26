import { IntelligenceOrchestrator } from '../core/IntelligenceOrchestrator';
import { ContextManager } from '../core/ContextManager';
import { CopilotMessage, CopilotSuggestion, CopilotAction, CopilotWorkflow, CopilotArtifact } from '../types/copilot';

describe('IntelligenceOrchestrator', () => {
  let contextManager: ContextManager;
  let intelligenceOrchestrator: IntelligenceOrchestrator;
  
  beforeEach(async () => {
    contextManager = new ContextManager();
    await contextManager.initialize();
    intelligenceOrchestrator = new IntelligenceOrchestrator(contextManager);
  });
  
  describe('Initialization', () => {
    it('should initialize with default features', () => {
      const features = intelligenceOrchestrator.getFeatures();
      
      expect(features).toBeDefined();
      expect(features.length).toBeGreaterThan(0);
      expect(features.some(f => f.id === 'proactive_suggestions')).toBe(true);
      expect(features.some(f => f.id === 'contextual_understanding')).toBe(true);
      expect(features.some(f => f.id === 'workflow_automation')).toBe(true);
      expect(features.some(f => f.id === 'artifact_generation')).toBe(true);
    });
    
    it('should have all features enabled by default', () => {
      const features = intelligenceOrchestrator.getFeatures();
      
      features.forEach(feature => {
        expect(feature.enabled).toBe(true);
      });
    });
  });
  
  describe('Input Processing', () => {
    it('should process input and return a response', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Hello',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('Hello', messages);
      
      expect(response).toBeDefined();
      expect(response.response).toBeDefined();
      expect(response.suggestions).toBeDefined();
      expect(response.actions).toBeDefined();
      expect(response.workflows).toBeDefined();
      expect(response.artifacts).toBeDefined();
    });
    
    it('should generate suggestions based on input', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Can you help me with code?',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('Can you help me with code?', messages);
      
      expect(response.suggestions).toBeDefined();
      expect(response.suggestions.length).toBeGreaterThan(0);
      
      // Check that suggestions have the required properties
      response.suggestions.forEach((suggestion: CopilotSuggestion) => {
        expect(suggestion.id).toBeDefined();
        expect(suggestion.title).toBeDefined();
        expect(suggestion.description).toBeDefined();
        expect(suggestion.type).toBeDefined();
        expect(suggestion.confidence).toBeGreaterThan(0);
        expect(suggestion.priority).toMatch(/^(low|medium|high)$/);
      });
    });
    
    it('should generate actions based on input', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Execute this code',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('Execute this code', messages);
      
      expect(response.actions).toBeDefined();
      expect(response.actions.length).toBeGreaterThan(0);
      
      // Check that actions have the required properties
      response.actions.forEach((action: CopilotAction) => {
        expect(action.id).toBeDefined();
        expect(action.title).toBeDefined();
        expect(action.description).toBeDefined();
        expect(action.pluginId).toBeDefined();
        expect(action.riskLevel).toMatch(/^(safe|privileged|evil-mode-only)$/);
      });
    });
    
    it('should generate workflows based on input', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'I need a code review workflow',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('I need a code review workflow', messages);
      
      expect(response.workflows).toBeDefined();
      expect(response.workflows.length).toBeGreaterThan(0);
      
      // Check that workflows have the required properties
      response.workflows.forEach((workflow: CopilotWorkflow) => {
        expect(workflow.id).toBeDefined();
        expect(workflow.title).toBeDefined();
        expect(workflow.description).toBeDefined();
        expect(workflow.steps).toBeDefined();
        expect(workflow.steps.length).toBeGreaterThan(0);
        expect(workflow.estimatedTime).toBeDefined();
        expect(workflow.complexity).toMatch(/^(basic|intermediate|advanced|expert)$/);
      });
    });
    
    it('should generate artifacts based on input', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Generate documentation for this code',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('Generate documentation for this code', messages);
      
      expect(response.artifacts).toBeDefined();
      expect(response.artifacts.length).toBeGreaterThan(0);
      
      // Check that artifacts have the required properties
      response.artifacts.forEach((artifact: CopilotArtifact) => {
        expect(artifact.id).toBeDefined();
        expect(artifact.title).toBeDefined();
        expect(artifact.description).toBeDefined();
        expect(artifact.type).toMatch(/^(code|documentation|analysis|test|other)$/);
        expect(artifact.content).toBeDefined();
        expect(artifact.language).toBeDefined();
      });
    });
  });
  
  describe('Feature Management', () => {
    it('should enable and disable features', () => {
      // Disable a feature
      const result = intelligenceOrchestrator.disableFeature('proactive_suggestions');
      expect(result).toBe(true);
      
      let feature = intelligenceOrchestrator.getFeatures().find(f => f.id === 'proactive_suggestions');
      expect(feature?.enabled).toBe(false);
      
      // Enable the feature again
      const result2 = intelligenceOrchestrator.enableFeature('proactive_suggestions');
      expect(result2).toBe(true);
      
      feature = intelligenceOrchestrator.getFeatures().find(f => f.id === 'proactive_suggestions');
      expect(feature?.enabled).toBe(true);
    });
    
    it('should get feature status', () => {
      const status = intelligenceOrchestrator.getFeatureStatus('proactive_suggestions');
      expect(status).toBe(true);
      
      intelligenceOrchestrator.disableFeature('proactive_suggestions');
      const statusAfterDisable = intelligenceOrchestrator.getFeatureStatus('proactive_suggestions');
      expect(statusAfterDisable).toBe(false);
    });
    
    it('should get enabled features', () => {
      intelligenceOrchestrator.disableFeature('proactive_suggestions');
      
      const enabledFeatures = intelligenceOrchestrator.getEnabledFeatures();
      
      expect(enabledFeatures).toBeDefined();
      expect(enabledFeatures.length).toBeGreaterThan(0);
      
      // Check that all returned features are enabled
      enabledFeatures.forEach(feature => {
        expect(feature.enabled).toBe(true);
      });
      
      // Check that the disabled feature is not in the list
      expect(enabledFeatures.some(f => f.id === 'proactive_suggestions')).toBe(false);
    });
  });
  
  describe('Action Execution', () => {
    it('should execute actions', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Execute this code',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('Execute this code', messages);
      const action = response.actions[0];
      
      if (action) {
        const result = await intelligenceOrchestrator.executeAction(action.id);
        expect(result).toBe(true);
      }
    });
    
    it('should return false for non-existent action', async () => {
      const result = await intelligenceOrchestrator.executeAction('non-existent-action');
      expect(result).toBe(false);
    });
  });
  
  describe('Workflow Execution', () => {
    it('should execute workflows', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'I need a code review workflow',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('I need a code review workflow', messages);
      const workflow = response.workflows[0];
      
      if (workflow) {
        const result = await intelligenceOrchestrator.executeWorkflow(workflow.id);
        expect(result).toBe(true);
      }
    });
    
    it('should return false for non-existent workflow', async () => {
      const result = await intelligenceOrchestrator.executeWorkflow('non-existent-workflow');
      expect(result).toBe(false);
    });
  });
  
  describe('Artifact Generation', () => {
    it('should generate artifacts', async () => {
      const messages: CopilotMessage[] = [
        {
          id: 'msg1',
          content: 'Generate documentation for this code',
          role: 'user',
          timestamp: new Date()
        }
      ];
      
      const response = await intelligenceOrchestrator.processInput('Generate documentation for this code', messages);
      const artifact = response.artifacts[0];
      
      if (artifact) {
        const result = await intelligenceOrchestrator.generateArtifact(artifact.id);
        expect(result).toBeDefined();
        expect(result?.id).toBe(artifact.id);
      }
    });
    
    it('should return null for non-existent artifact', async () => {
      const result = await intelligenceOrchestrator.generateArtifact('non-existent-artifact');
      expect(result).toBeNull();
    });
  });
  
  describe('Plugin Management', () => {
    it('should add and remove plugins', () => {
      const plugin = {
        id: 'test-plugin',
        name: 'Test Plugin',
        description: 'A test plugin',
        version: '1.0.0',
        enabled: true
      };
      
      // Add plugin
      intelligenceOrchestrator.addPlugin(plugin);
      
      const plugins = intelligenceOrchestrator.getPlugins();
      expect(plugins.some(p => p.id === 'test-plugin')).toBe(true);
      
      // Remove plugin
      const result = intelligenceOrchestrator.removePlugin('test-plugin');
      expect(result).toBe(true);
      
      const pluginsAfterRemove = intelligenceOrchestrator.getPlugins();
      expect(pluginsAfterRemove.some(p => p.id === 'test-plugin')).toBe(false);
    });
    
    it('should enable and disable plugins', () => {
      const plugin = {
        id: 'test-plugin',
        name: 'Test Plugin',
        description: 'A test plugin',
        version: '1.0.0',
        enabled: true
      };
      
      intelligenceOrchestrator.addPlugin(plugin);
      
      // Disable plugin
      const result = intelligenceOrchestrator.disablePlugin('test-plugin');
      expect(result).toBe(true);
      
      let plugins = intelligenceOrchestrator.getPlugins();
      let testPlugin = plugins.find(p => p.id === 'test-plugin');
      expect(testPlugin?.enabled).toBe(false);
      
      // Enable plugin
      const result2 = intelligenceOrchestrator.enablePlugin('test-plugin');
      expect(result2).toBe(true);
      
      plugins = intelligenceOrchestrator.getPlugins();
      testPlugin = plugins.find(p => p.id === 'test-plugin');
      expect(testPlugin?.enabled).toBe(true);
    });
    
    it('should get enabled plugins', () => {
      const plugin1 = {
        id: 'test-plugin-1',
        name: 'Test Plugin 1',
        description: 'A test plugin',
        version: '1.0.0',
        enabled: true
      };
      
      const plugin2 = {
        id: 'test-plugin-2',
        name: 'Test Plugin 2',
        description: 'Another test plugin',
        version: '1.0.0',
        enabled: false
      };
      
      intelligenceOrchestrator.addPlugin(plugin1);
      intelligenceOrchestrator.addPlugin(plugin2);
      
      const enabledPlugins = intelligenceOrchestrator.getEnabledPlugins();
      
      expect(enabledPlugins).toBeDefined();
      expect(enabledPlugins.length).toBe(1);
      expect(enabledPlugins.some(p => p.id === 'test-plugin-1')).toBe(true);
      expect(enabledPlugins.some(p => p.id === 'test-plugin-2')).toBe(false);
    });
  });
  
  describe('Data Updates', () => {
    it('should update suggestions', () => {
      const suggestions: CopilotSuggestion[] = [
        {
          id: 'test-suggestion',
          title: 'Test Suggestion',
          description: 'A test suggestion',
          type: 'action',
          confidence: 0.8,
          priority: 'medium'
        }
      ];
      
      intelligenceOrchestrator.updateSuggestions(suggestions);
      
      const updatedSuggestions = intelligenceOrchestrator.getSuggestions();
      expect(updatedSuggestions).toEqual(suggestions);
    });
    
    it('should update actions', () => {
      const actions: CopilotAction[] = [
        {
          id: 'test-action',
          title: 'Test Action',
          description: 'A test action',
          pluginId: 'test-plugin',
          riskLevel: 'safe'
        }
      ];
      
      intelligenceOrchestrator.updateActions(actions);
      
      const updatedActions = intelligenceOrchestrator.getActions();
      expect(updatedActions).toEqual(actions);
    });
    
    it('should update workflows', () => {
      const workflows: CopilotWorkflow[] = [
        {
          id: 'test-workflow',
          title: 'Test Workflow',
          description: 'A test workflow',
          steps: ['Step 1', 'Step 2'],
          estimatedTime: '10 minutes',
          complexity: 'basic',
          metadata: {}
        }
      ];
      
      intelligenceOrchestrator.updateWorkflows(workflows);
      
      const updatedWorkflows = intelligenceOrchestrator.getWorkflows();
      expect(updatedWorkflows).toEqual(workflows);
    });
    
    it('should update artifacts', () => {
      const artifacts: CopilotArtifact[] = [
        {
          id: 'test-artifact',
          title: 'Test Artifact',
          description: 'A test artifact',
          type: 'code',
          content: 'console.log("Hello, world!");',
          language: 'javascript',
          metadata: {}
        }
      ];
      
      intelligenceOrchestrator.updateArtifacts(artifacts);
      
      const updatedArtifacts = intelligenceOrchestrator.getArtifacts();
      expect(updatedArtifacts).toEqual(artifacts);
    });
  });
});