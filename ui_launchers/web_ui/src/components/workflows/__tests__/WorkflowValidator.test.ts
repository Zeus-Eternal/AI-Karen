import { describe, it, expect } from 'vitest';
import { WorkflowValidator } from '../WorkflowValidator';
import { WorkflowDefinition } from '@/types/workflows';

describe('WorkflowValidator', () => {
  const createBasicWorkflow = (): WorkflowDefinition => ({
    id: 'test-workflow',
    name: 'Test Workflow',
    description: 'A test workflow',
    version: '1.0.0',
    nodes: [],
    edges: [],
    variables: [],
    tags: [],
    metadata: {
      createdAt: new Date(),
      updatedAt: new Date(),
      createdBy: 'test-user',
      status: 'draft'
    }

  describe('basic validation', () => {
    it('should fail validation for empty workflow', async () => {
      const workflow = createBasicWorkflow();
      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].type).toBe('missing_connection');
      expect(result.errors[0].message).toContain('at least one node');

    it('should pass validation for single node workflow', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [{
        id: 'node1',
        type: 'input',
        position: { x: 0, y: 0 },
        data: {
          label: 'Input Node',
          config: {},
          inputs: [],
          outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
        }
      }];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);


  describe('connection validation', () => {
    it('should warn about disconnected nodes', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'input',
          position: { x: 0, y: 0 },
          data: {
            label: 'Input Node',
            config: {},
            inputs: [],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'output',
          position: { x: 200, y: 0 },
          data: {
            label: 'Output Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string', required: true }],
            outputs: []
          }
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(false);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings.some(w => w.message.includes('not connected'))).toBe(true);

    it('should validate required input connections', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'input',
          position: { x: 0, y: 0 },
          data: {
            label: 'Input Node',
            config: {},
            inputs: [],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'llm',
          position: { x: 200, y: 0 },
          data: {
            label: 'LLM Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Prompt', type: 'string', required: true }],
            outputs: [{ id: 'out1', name: 'Response', type: 'string' }]
          }
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.type === 'missing_connection')).toBe(true);
      expect(result.errors.some(e => e.message.includes('Required input'))).toBe(true);


  describe('circular dependency detection', () => {
    it('should detect simple circular dependencies', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'custom',
          position: { x: 0, y: 0 },
          data: {
            label: 'Node 1',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'custom',
          position: { x: 200, y: 0 },
          data: {
            label: 'Node 2',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        }
      ];
      workflow.edges = [
        {
          id: 'edge1',
          source: 'node1',
          target: 'node2',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        },
        {
          id: 'edge2',
          source: 'node2',
          target: 'node1',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.type === 'circular_dependency')).toBe(true);

    it('should detect complex circular dependencies', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'custom',
          position: { x: 0, y: 0 },
          data: {
            label: 'Node 1',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'custom',
          position: { x: 200, y: 0 },
          data: {
            label: 'Node 2',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node3',
          type: 'custom',
          position: { x: 400, y: 0 },
          data: {
            label: 'Node 3',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        }
      ];
      workflow.edges = [
        {
          id: 'edge1',
          source: 'node1',
          target: 'node2',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        },
        {
          id: 'edge2',
          source: 'node2',
          target: 'node3',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        },
        {
          id: 'edge3',
          source: 'node3',
          target: 'node1',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.type === 'circular_dependency')).toBe(true);


  describe('type compatibility validation', () => {
    it('should validate compatible types', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'input',
          position: { x: 0, y: 0 },
          data: {
            label: 'Input Node',
            config: {},
            inputs: [],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'output',
          position: { x: 200, y: 0 },
          data: {
            label: 'Output Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: []
          }
        }
      ];
      workflow.edges = [
        {
          id: 'edge1',
          source: 'node1',
          target: 'node2',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.errors.some(e => e.type === 'type_mismatch')).toBe(false);

    it('should detect type mismatches', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'input',
          position: { x: 0, y: 0 },
          data: {
            label: 'Input Node',
            config: {},
            inputs: [],
            outputs: [{ id: 'out1', name: 'Output', type: 'number' }]
          }
        },
        {
          id: 'node2',
          type: 'output',
          position: { x: 200, y: 0 },
          data: {
            label: 'Output Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'object' }],
            outputs: []
          }
        }
      ];
      workflow.edges = [
        {
          id: 'edge1',
          source: 'node1',
          target: 'node2',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.type === 'type_mismatch')).toBe(true);

    it('should allow any type to accept any input', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'input',
          position: { x: 0, y: 0 },
          data: {
            label: 'Input Node',
            config: {},
            inputs: [],
            outputs: [{ id: 'out1', name: 'Output', type: 'object' }]
          }
        },
        {
          id: 'node2',
          type: 'output',
          position: { x: 200, y: 0 },
          data: {
            label: 'Output Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'any' }],
            outputs: []
          }
        }
      ];
      workflow.edges = [
        {
          id: 'edge1',
          source: 'node1',
          target: 'node2',
          sourceHandle: 'out1',
          targetHandle: 'in1'
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.errors.some(e => e.type === 'type_mismatch')).toBe(false);


  describe('performance warnings', () => {
    it('should warn about large workflows', async () => {
      const workflow = createBasicWorkflow();
      
      // Create 51 nodes to trigger the warning
      for (let i = 0; i < 51; i++) {
        workflow.nodes.push({
          id: `node${i}`,
          type: 'custom',
          position: { x: i * 100, y: 0 },
          data: {
            label: `Node ${i}`,
            config: {},
            inputs: [],
            outputs: []
          }

      }

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.warnings.some(w => w.type === 'performance')).toBe(true);
      expect(result.warnings.some(w => w.message.includes('Large workflow'))).toBe(true);


  describe('best practice warnings', () => {
    it('should warn about missing input nodes', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'llm',
          position: { x: 0, y: 0 },
          data: {
            label: 'LLM Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Prompt', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Response', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'output',
          position: { x: 200, y: 0 },
          data: {
            label: 'Output Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Input', type: 'string' }],
            outputs: []
          }
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.warnings.some(w => w.message.includes('no input nodes'))).toBe(true);

    it('should warn about missing output nodes', async () => {
      const workflow = createBasicWorkflow();
      workflow.nodes = [
        {
          id: 'node1',
          type: 'input',
          position: { x: 0, y: 0 },
          data: {
            label: 'Input Node',
            config: {},
            inputs: [],
            outputs: [{ id: 'out1', name: 'Output', type: 'string' }]
          }
        },
        {
          id: 'node2',
          type: 'llm',
          position: { x: 200, y: 0 },
          data: {
            label: 'LLM Node',
            config: {},
            inputs: [{ id: 'in1', name: 'Prompt', type: 'string' }],
            outputs: [{ id: 'out1', name: 'Response', type: 'string' }]
          }
        }
      ];

      const result = await WorkflowValidator.validate(workflow);
      
      expect(result.warnings.some(w => w.message.includes('no output nodes'))).toBe(true);


