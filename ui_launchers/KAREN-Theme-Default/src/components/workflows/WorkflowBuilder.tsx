// ui_launchers/KAREN-Theme-Default/src/components/workflows/WorkflowBuilder.tsx
"use client";

import * as React from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Connection,
  ReactFlowProvider,
  ReactFlowInstance,
  NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeTemplate, WorkflowValidationResult, NodePort } from '@/types/workflows';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';

import { AlertTriangle, CheckCircle, Copy, Eye, EyeOff, Play, Save, Trash2 } from 'lucide-react';
import { WorkflowNodeComponent } from './WorkflowNodeComponent';
import { NodeLibrary } from './NodeLibrary';
import { WorkflowValidator } from './WorkflowValidator';

export interface WorkflowBuilderProps {
  workflow?: WorkflowDefinition;
  onSave?: (workflow: WorkflowDefinition) => void;
  onTest?: (workflow: WorkflowDefinition) => Promise<unknown>;
  readOnly?: boolean;
  className?: string;
}

const nodeTypes: NodeTypes = {
  workflowNode: WorkflowNodeComponent,
};

export function WorkflowBuilder({
  workflow,
  onSave,
  onTest,
  readOnly = false,
  className = '',
}: WorkflowBuilderProps) {
  const reactFlowWrapper = React.useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);

  // Convert workflow nodes/edges to ReactFlow format
  const initialNodes: Node[] = React.useMemo(() =>
    workflow?.nodes.map(node => ({
      id: node.id,
      type: 'workflowNode',
      position: node.position,
      data: node.data,
      style: node.style,
    })) || [], [workflow]
  );

  const initialEdges: Edge[] = React.useMemo(() =>
    workflow?.edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle,
      targetHandle: edge.targetHandle,
      type: edge.type || 'default',
      animated: edge.animated,
      style: edge.style,
      data: edge.data,
    })) || [], [workflow]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = React.useState<Node | null>(null);
  const selectedNodeData = selectedNode?.data as WorkflowNode['data'] | undefined;
  const [validationResult, setValidationResult] = React.useState<WorkflowValidationResult | null>(null);
  const [isValidating, setIsValidating] = React.useState(false);
  const [isTesting, setIsTesting] = React.useState(false);
  const [showMiniMap, setShowMiniMap] = React.useState(true);
  const [showBackground, setShowBackground] = React.useState(true);

  const onConnect = React.useCallback(
    (params: Connection) => {
      if (readOnly) return;
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges, readOnly]
  );

  const onInit = React.useCallback((instance: ReactFlowInstance) => {
    setReactFlowInstance(instance);
  }, []);

  const onDragOver = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = React.useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      if (!reactFlowInstance || readOnly) return;

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      const payload = event.dataTransfer.getData('application/reactflow');
      if (!payload) return;

      let nodeTemplate: NodeTemplate;
      try {
        nodeTemplate = JSON.parse(payload) as NodeTemplate;
      } catch (error) {
        console.error('Failed to parse node template from drag event', error);
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: `${nodeTemplate.id}-${Date.now()}`,
        type: 'workflowNode',
        position,
        data: {
          label: nodeTemplate.name,
          description: nodeTemplate.description,
          nodeType: nodeTemplate.id,
          config: { ...nodeTemplate.config?.defaults },
          inputs: nodeTemplate.inputs,
          outputs: nodeTemplate.outputs,
        },
      };
      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes, readOnly]
  );

  const onNodeClick = React.useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = React.useCallback(() => {
    setSelectedNode(null);
  }, []);

  const convertToWorkflowDefinition = React.useCallback((): WorkflowDefinition => {
    const allowedNodeTypes: WorkflowNode['type'][] = ['input', 'output', 'llm', 'memory', 'plugin', 'condition', 'loop', 'custom'];

    const workflowNodes: WorkflowNode[] = nodes.map((node) => {
      const nodeData = node.data as WorkflowNode['data'];
      const resolvedType = allowedNodeTypes.includes(nodeData?.nodeType as WorkflowNode['type'])
        ? (nodeData.nodeType as WorkflowNode['type'])
        : 'custom';

      return {
        id: node.id,
        type: resolvedType,
        position: node.position,
        data: nodeData,
        style: node.style
          ? (node.style as unknown as Record<string, unknown>)
          : undefined,
      };
    });

    const allowedEdgeTypes: WorkflowEdge['type'][] = ['default', 'straight', 'step', 'smoothstep'];

    const workflowEdges: WorkflowEdge[] = edges.map((edge) => {
      const normalizedType = allowedEdgeTypes.includes(edge.type as WorkflowEdge['type'])
        ? (edge.type as WorkflowEdge['type'])
        : 'default';

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle ?? undefined,
        targetHandle: edge.targetHandle ?? undefined,
        type: normalizedType,
        animated: edge.animated,
        style: edge.style
          ? (edge.style as unknown as Record<string, unknown>)
          : undefined,
        data: edge.data,
      };
    });

    return {
      id: workflow?.id || `workflow-${Date.now()}`,
      name: workflow?.name || 'Untitled Workflow',
      description: workflow?.description || '',
      version: workflow?.version || '1.0.0',
      nodes: workflowNodes,
      edges: workflowEdges,
      variables: workflow?.variables || [],
      tags: workflow?.tags || [],
      metadata: workflow?.metadata || {
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'current-user',
        status: 'draft',
      },
    };
  }, [nodes, edges, workflow]);

  const validateWorkflow = React.useCallback(async () => {
    setIsValidating(true);
    try {
      const workflowDef = convertToWorkflowDefinition();
      const result = await WorkflowValidator.validate(workflowDef);
      setValidationResult(result);
    } catch (error) {
      console.error('Workflow validation failed', error);
    } finally {
      setIsValidating(false);
    }
  }, [convertToWorkflowDefinition]);

  const testWorkflow = React.useCallback(async () => {
    if (!onTest) return;
    setIsTesting(true);
    try {
      const workflowDef = convertToWorkflowDefinition();
      await onTest(workflowDef);
    } catch (error) {
      console.error('Workflow test failed', error);
    } finally {
      setIsTesting(false);
    }
  }, [convertToWorkflowDefinition, onTest]);

  const handleSave = React.useCallback(() => {
    if (!onSave) return;
    const workflowDef = convertToWorkflowDefinition();
    onSave(workflowDef);
  }, [convertToWorkflowDefinition, onSave]);

  const deleteSelectedNode = React.useCallback(() => {
    if (!selectedNode || readOnly) return;
    setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
    setEdges((eds) => eds.filter((edge) =>
      edge.source !== selectedNode.id && edge.target !== selectedNode.id
    ));
    setSelectedNode(null);
  }, [selectedNode, setNodes, setEdges, readOnly]);

  const duplicateSelectedNode = React.useCallback(() => {
    if (!selectedNode || readOnly) return;
    const newNode: Node = {
      ...selectedNode,
      id: `${selectedNode.id}-copy-${Date.now()}`,
      position: {
        x: selectedNode.position.x + 50,
        y: selectedNode.position.y + 50,
      },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [selectedNode, setNodes, readOnly]);

  return (
    <div className={`flex h-full ${className}`}>
      {/* Node Library Sidebar */}
      <div className="w-80 border-r bg-background ">
        <div className="p-4 sm:p-4 md:p-6">
          <h3 className="text-lg font-semibold mb-4">Node Library</h3>
          <NodeLibrary readOnly={readOnly} />
        </div>
      </div>

      {/* Main Workflow Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="border-b p-4 sm:p-4 md:p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold">
                {workflow?.name || 'Untitled Workflow'}
              </h2>
              {workflow?.metadata.status && (
                <Badge variant={workflow.metadata.status === 'active' ? 'default' : 'secondary'}>
                  {workflow.metadata.status}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                aria-label={showMiniMap ? 'Hide minimap' : 'Show minimap'}
                variant="outline"
                size="sm"
                onClick={() => setShowMiniMap(!showMiniMap)}
              >
                {showMiniMap ? <EyeOff className="h-4 w-4 " /> : <Eye className="h-4 w-4 " />}
              </Button>
              <Button
                aria-label={showBackground ? 'Hide background grid' : 'Show background grid'}
                variant="outline"
                size="sm"
                onClick={() => setShowBackground(!showBackground)}
              >
                {showBackground ? <EyeOff className="h-4 w-4 " /> : <Eye className="h-4 w-4 " />}
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <Button
                aria-label="Validate workflow"
                variant="outline"
                size="sm"
                onClick={validateWorkflow}
                disabled={isValidating}
              >
                <CheckCircle className="h-4 w-4 mr-2 " />
                <span className="hidden sm:inline">Validate</span>
              </Button>
              {onTest && (
                <Button
                  aria-label="Test workflow"
                  variant="outline"
                  size="sm"
                  onClick={testWorkflow}
                  disabled={isTesting}
                >
                  <Play className="h-4 w-4 mr-2 " />
                  <span className="hidden sm:inline">Test</span>
                </Button>
              )}
              {onSave && !readOnly && (
                <Button
                  aria-label="Save workflow"
                  size="sm"
                  onClick={handleSave}
                >
                  <Save className="h-4 w-4 mr-2 " />
                  <span className="hidden sm:inline">Save</span>
                </Button>
              )}
            </div>
          </div>
          {/* Validation Results */}
          {validationResult && (
            <div className="mt-4">
              {validationResult.errors.length > 0 && (
                <Alert variant="destructive" className="mb-2">
                  <AlertTriangle className="h-4 w-4 " />
                  <AlertDescription>
                    {validationResult.errors.length} error(s) found. Please fix them before saving.
                  </AlertDescription>
                </Alert>
              )}
              {validationResult.warnings.length > 0 && (
                <Alert className="mb-2">
                  <AlertTriangle className="h-4 w-4 " />
                  <AlertDescription>
                    {validationResult.warnings.length} warning(s) found.
                  </AlertDescription>
                </Alert>
              )}
              {validationResult.valid && (
                <Alert className="mb-2">
                  <CheckCircle className="h-4 w-4 " />
                  <AlertDescription>
                    Workflow validation passed successfully.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </div>

        {/* ReactFlow Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={onInit}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="top-right"
          >
            <Controls />
            {showMiniMap && <MiniMap />}
            {showBackground && <Background variant={BackgroundVariant.Dots} gap={12} size={1} />}
          </ReactFlow>
        </div>
      </div>

      {/* Properties Panel */}
      {selectedNode && (
        <div className="w-80 border-l bg-background ">
          <div className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Node Properties</h3>
              <div className="flex gap-2">
                {!readOnly && (
                  <>
                  <Button
                    aria-label="Duplicate node"
                    variant="outline"
                    size="sm"
                    onClick={duplicateSelectedNode}
                  >
                    <Copy className="h-4 w-4 " />
                  </Button>
                  <Button
                    aria-label="Delete node"
                    variant="outline"
                    size="sm"
                    onClick={deleteSelectedNode}
                  >
                    <Trash2 className="h-4 w-4 " />
                  </Button>
                  </>
                )}
              </div>
            </div>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm md:text-base lg:text-lg">{selectedNodeData?.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Description</label>
                    <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                      {selectedNodeData?.description || 'No description available'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Type</label>
                    <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                      {selectedNodeData?.nodeType || 'custom'}
                    </p>
                  </div>
                  {selectedNodeData?.inputs && selectedNodeData.inputs.length > 0 && (
                    <div>
                      <label className="text-sm font-medium md:text-base lg:text-lg">Inputs</label>
                      <div className="mt-2 space-y-1">
                        {selectedNodeData.inputs?.map((input: NodePort) => (
                          <div key={input.id} className="text-sm md:text-base lg:text-lg">
                            <span className="font-medium">{input.name}</span>
                            <span className="text-muted-foreground ml-2">({input.type})</span>
                            {input.required && <span className="text-red-500 ml-1">*</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedNodeData?.outputs && selectedNodeData.outputs.length > 0 && (
                    <div>
                      <label className="text-sm font-medium md:text-base lg:text-lg">Outputs</label>
                      <div className="mt-2 space-y-1">
                        {selectedNodeData.outputs?.map((output: NodePort) => (
                          <div key={output.id} className="text-sm md:text-base lg:text-lg">
                            <span className="font-medium">{output.name}</span>
                            <span className="text-muted-foreground ml-2">({output.type})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export function WorkflowBuilderProvider({ children }: { children: React.ReactNode }) {
  return (
    <ReactFlowProvider>
      {children}
    </ReactFlowProvider>
  );
}
