"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { WorkflowDefinition, WorkflowValidationResult, ValidationError, ValidationWarning } from '@/types/workflows';

export class WorkflowValidator {
  static async validate(workflow: WorkflowDefinition): Promise<WorkflowValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Check for basic workflow structure
    if (!workflow.nodes || workflow.nodes.length === 0) {
      errors.push({
        id: 'no-nodes',
        type: 'missing_connection',
        message: 'Workflow must contain at least one node',
        severity: 'error',
      });
    }

    // Check for disconnected nodes
    const connectedNodes = new Set<string>();
    workflow.edges.forEach(edge => {
      connectedNodes.add(edge.source);
      connectedNodes.add(edge.target);
    });

    workflow.nodes.forEach(node => {
      if (!connectedNodes.has(node.id) && workflow.nodes.length > 1) {
        warnings.push({
          id: `disconnected-${node.id}`,
          type: 'best_practice',
          nodeId: node.id,
          message: `Node "${node.data.label}" is not connected to any other nodes`,
          suggestion: 'Connect this node to the workflow or remove it',
        });
      }
    });

    // Check for circular dependencies
    const circularDependencies = this.detectCircularDependencies(workflow);
    circularDependencies.forEach(cycle => {
      errors.push({
        id: `circular-${cycle.join('-')}`,
        type: 'circular_dependency',
        message: `Circular dependency detected: ${cycle.join(' → ')}`,
        severity: 'error',
      });
    });

    // Check for missing required inputs
    workflow.nodes.forEach(node => {
      if (node.data.inputs) {
        node.data.inputs.forEach(input => {
          if (input.required) {
            const hasConnection = workflow.edges.some(edge =>
              edge.target === node.id && edge.targetHandle === input.id
            );

            if (!hasConnection) {
              errors.push({
                id: `missing-input-${node.id}-${input.id}`,
                type: 'missing_connection',
                nodeId: node.id,
                message: `Required input "${input.name}" is not connected in node "${node.data.label}"`,
                severity: 'error',
              });
            }
          }
        });
      }
    });

    // Check for type mismatches
    workflow.edges.forEach(edge => {
      const sourceNode = workflow.nodes.find(n => n.id === edge.source);
      const targetNode = workflow.nodes.find(n => n.id === edge.target);

      if (sourceNode && targetNode) {
        const sourceOutput = sourceNode.data.outputs?.find(o => o.id === edge.sourceHandle);
        const targetInput = targetNode.data.inputs?.find(i => i.id === edge.targetHandle);

        if (sourceOutput && targetInput) {
          if (!this.areTypesCompatible(sourceOutput.type, targetInput.type)) {
            errors.push({
              id: `type-mismatch-${edge.id}`,
              type: 'type_mismatch',
              edgeId: edge.id,
              message: `Type mismatch: Cannot connect ${sourceOutput.type} to ${targetInput.type}`,
              severity: 'error',
            });
          }
        }
      }
    });

    // Check for performance issues
    if (workflow.nodes.length > 50) {
      warnings.push({
        id: 'large-workflow',
        type: 'performance',
        message: 'Large workflow detected. Consider breaking it into smaller sub-workflows',
        suggestion: 'Split complex workflows into reusable sub-workflows',
      });
    }

    // Check for input/output nodes
    const hasInputNode = workflow.nodes.some(node => node.type === 'input');
    const hasOutputNode = workflow.nodes.some(node => node.type === 'output');

    if (!hasInputNode && workflow.nodes.length > 1) {
      warnings.push({
        id: 'no-input',
        type: 'best_practice',
        message: 'Workflow has no input nodes',
        suggestion: 'Add an input node to define how data enters the workflow',
      });
    }

    if (!hasOutputNode && workflow.nodes.length > 1) {
      warnings.push({
        id: 'no-output',
        type: 'best_practice',
        message: 'Workflow has no output nodes',
        suggestion: 'Add an output node to define how results are returned',
      });
    }

    // Check for deprecated node types
    workflow.nodes.forEach(node => {
      if (this.isDeprecatedNodeType(node.type)) {
        warnings.push({
          id: `deprecated-${node.id}`,
          type: 'deprecated',
          nodeId: node.id,
          message: `Node type "${node.type}" is deprecated`,
          suggestion: 'Consider upgrading to a newer node type',
        });
      }
    });

    return {
      valid: errors.length === 0,
      errors,
      warnings,
    };
  }

  private static detectCircularDependencies(workflow: WorkflowDefinition): string[][] {
    const graph = new Map<string, string[]>();
    const cycles: string[][] = [];

    // Build adjacency list
    workflow.nodes.forEach(node => {
      graph.set(node.id, []);
    });

    workflow.edges.forEach(edge => {
      const neighbors = graph.get(edge.source) || [];
      neighbors.push(edge.target);
      graph.set(edge.source, neighbors);
    });

    // DFS to detect cycles
    const visited = new Set<string>();
    const recursionStack = new Set<string>();
    const path: string[] = [];

    const dfs = (nodeId: string): boolean => {
      visited.add(nodeId);
      recursionStack.add(nodeId);
      path.push(nodeId);

      const neighbors = graph.get(nodeId) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          if (dfs(neighbor)) {
            return true;
          }
        } else if (recursionStack.has(neighbor)) {
          // Found a cycle
          const cycleStart = path.indexOf(neighbor);
          const cycle = path.slice(cycleStart);
          cycle.push(neighbor); // Complete the cycle
          cycles.push(cycle);
          return true;
        }
      }

      recursionStack.delete(nodeId);
      path.pop();
      return false;
    };

    workflow.nodes.forEach(node => {
      if (!visited.has(node.id)) {
        dfs(node.id);
      }
    });

    return cycles;
  }

  private static areTypesCompatible(sourceType: string, targetType: string): boolean {
    if (sourceType === targetType) return true;

    // Any type accepts anything
    if (targetType === 'any') return true;

    // String can be converted to most types
    if (sourceType === 'string' && ['number', 'boolean'].includes(targetType)) return true;

    // Number can be converted to string
    if (sourceType === 'number' && targetType === 'string') return true;

    // Boolean can be converted to string
    if (sourceType === 'boolean' && targetType === 'string') return true;

    // Object and array are compatible in some cases
    if (sourceType === 'object' && targetType === 'array') return true;

    return false;
  }

  private static isDeprecatedNodeType(nodeType: string): boolean {
    const deprecatedTypes = ['legacy-llm', 'old-memory', 'deprecated-plugin'];
    return deprecatedTypes.includes(nodeType);
  }
}

// React component for displaying validation results
export interface WorkflowValidationDisplayProps {
  validationResult: WorkflowValidationResult;
  onFixError?: (errorId: string) => void;
}

export function WorkflowValidationDisplay({ 
  validationResult, 
  onFixError 
}: WorkflowValidationDisplayProps) {
  if (validationResult.valid && validationResult.warnings.length === 0) {
    return (
      <div className="text-green-600 text-sm flex items-center gap-2 md:text-base lg:text-lg">
        <div className="w-2 h-2 bg-green-500 rounded-full " />
        <span>Workflow is valid!</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {validationResult.errors.map(error => (
        <div key={error.id} className="flex items-start gap-2 p-2 bg-red-50 border border-red-200 rounded text-sm md:text-base lg:text-lg">
          <div className="w-2 h-2 bg-red-500 rounded-full mt-1.5 flex-shrink-0 " />
          <div className="flex-1">
            <p className="text-red-800 font-medium">Error: {error.message}</p>
            {error.nodeId && (
              <p className="text-red-600 text-xs mt-1 sm:text-sm md:text-base">Node: {error.nodeId}</p>
            )}
          </div>
          {onFixError && (
            <Button
              onClick={() => onFixError(error.id)}
              className="text-red-600 hover:text-red-800 text-xs underline sm:text-sm md:text-base"
            >
              Fix Error
            </Button>
          )}
        </div>
      ))}

      {validationResult.warnings.map(warning => (
        <div key={warning.id} className="flex items-start gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm md:text-base lg:text-lg">
          <div className="w-2 h-2 bg-yellow-500 rounded-full mt-1.5 flex-shrink-0 " />
          <div className="flex-1">
            <p className="text-yellow-800 font-medium">Warning: {warning.message}</p>
            {warning.suggestion && (
              <p className="text-yellow-700 text-xs mt-1 sm:text-sm md:text-base">Suggestion: {warning.suggestion}</p>
            )}
            {warning.nodeId && (
              <p className="text-yellow-600 text-xs mt-1 sm:text-sm md:text-base">Node: {warning.nodeId}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
