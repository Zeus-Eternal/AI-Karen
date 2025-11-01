'use client';

import React, { useCallback, useMemo, useState, useRef } from 'react';
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
  EdgeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeTemplate, WorkflowValidationResult } from '@/types/workflows';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Play, 
  Save, 
  Download, 
  Upload, 
  Trash2, 
  Settings, 
  AlertTriangle,
  CheckCircle,
  Plus,
  Copy,
  Eye,
  EyeOff
} from 'lucide-react';

import { WorkflowNodeComponent } from './WorkflowNodeComponent';
import { NodeLibrary } from './NodeLibrary';
import { WorkflowValidator } from './WorkflowValidator';
import { WorkflowTester } from './WorkflowTester';

interface WorkflowBuilderProps {
  workflow?: WorkflowDefinition;
  onSave?: (workflow: WorkflowDefinition) => void;
  onTest?: (workflow: WorkflowDefinition) => Promise<any>;
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
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  
  // Convert workflow nodes/edges to ReactFlow format
  const initialNodes: Node[] = useMemo(() => 
    workflow?.nodes.map(node => ({
      id: node.id,
      type: 'workflowNode',
      position: node.position,
      data: node.data,
      style: node.style,
    })) || [], [workflow]
  );

  const initialEdges: Edge[] = useMemo(() => 
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
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [validationResult, setValidationResult] = useState<WorkflowValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [showMiniMap, setShowMiniMap] = useState(true);
  const [showBackground, setShowBackground] = useState(true);

  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;
      setEdges((eds) => addEdge(params, eds));
    },
    [setEdges, readOnly]
  );

  const onInit = useCallback((instance: ReactFlowInstance) => {
    setReactFlowInstance(instance);
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      if (!reactFlowInstance || readOnly) return;

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      const nodeTemplate = JSON.parse(
        event.dataTransfer.getData('application/reactflow')
      ) as NodeTemplate;

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
          config: nodeTemplate.config.defaults,
          inputs: nodeTemplate.inputs,
          outputs: nodeTemplate.outputs,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, setNodes, readOnly]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const validateWorkflow = useCallback(async () => {
    setIsValidating(true);
    try {
      const workflowDef = convertToWorkflowDefinition();
      const result = await WorkflowValidator.validate(workflowDef);
      setValidationResult(result);
    } catch (error) {
      console.error('Validation error:', error);
    } finally {
      setIsValidating(false);
    }
  }, [nodes, edges]);

  const testWorkflow = useCallback(async () => {
    if (!onTest) return;
    
    setIsTesting(true);
    try {
      const workflowDef = convertToWorkflowDefinition();
      await onTest(workflowDef);
    } catch (error) {
      console.error('Test error:', error);
    } finally {
      setIsTesting(false);
    }
  }, [nodes, edges, onTest]);

  const convertToWorkflowDefinition = useCallback((): WorkflowDefinition => {
    const workflowNodes: WorkflowNode[] = nodes.map(node => ({
      id: node.id,
      type: node.data.nodeType || 'custom',
      position: node.position,
      data: node.data,
      style: node.style,
    }));

    const workflowEdges: WorkflowEdge[] = edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      sourceHandle: edge.sourceHandle ?? undefined,
      targetHandle: edge.targetHandle ?? undefined,
      type: edge.type as 'default' | 'straight' | 'step' | 'smoothstep' | undefined,
      animated: edge.animated,
      style: edge.style,
      data: edge.data,
    }));

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

  const handleSave = useCallback(() => {
    if (!onSave) return;
    const workflowDef = convertToWorkflowDefinition();
    onSave(workflowDef);
  }, [convertToWorkflowDefinition, onSave]);

  const deleteSelectedNode = useCallback(() => {
    if (!selectedNode || readOnly) return;
    
    setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id));
    setEdges((eds) => eds.filter((edge) => 
      edge.source !== selectedNode.id && edge.target !== selectedNode.id
    ));
    setSelectedNode(null);
  }, [selectedNode, setNodes, setEdges, readOnly]);

  const duplicateSelectedNode = useCallback(() => {
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
      <div className="w-80 border-r bg-background">
        <div className="p-4">
          <h3 className="text-lg font-semibold mb-4">Node Library</h3>
          <NodeLibrary readOnly={readOnly} />
        </div>
      </div>

      {/* Main Workflow Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="border-b p-4">
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
                variant="outline"
                size="sm"
                onClick={() => setShowMiniMap(!showMiniMap)}
              >
                {showMiniMap ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                MiniMap
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowBackground(!showBackground)}
              >
                {showBackground ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                Grid
              </Button>
              
              <Separator orientation="vertical" className="h-6" />
              
              <Button
                variant="outline"
                size="sm"
                onClick={validateWorkflow}
                disabled={isValidating}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Validate
              </Button>
              
              {onTest && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={testWorkflow}
                  disabled={isTesting}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Test
                </Button>
              )}
              
              {onSave && !readOnly && (
                <Button
                  size="sm"
                  onClick={handleSave}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
              )}
            </div>
          </div>
          
          {/* Validation Results */}
          {validationResult && (
            <div className="mt-4">
              {validationResult.errors.length > 0 && (
                <Alert variant="destructive" className="mb-2">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    {validationResult.errors.length} error(s) found. Please fix them before saving.
                  </AlertDescription>
                </Alert>
              )}
              
              {validationResult.warnings.length > 0 && (
                <Alert className="mb-2">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    {validationResult.warnings.length} warning(s) found.
                  </AlertDescription>
                </Alert>
              )}
              
              {validationResult.valid && (
                <Alert className="mb-2">
                  <CheckCircle className="h-4 w-4" />
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
        <div className="w-80 border-l bg-background">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Node Properties</h3>
              <div className="flex gap-2">
                {!readOnly && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={duplicateSelectedNode}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={deleteSelectedNode}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </>
                )}
              </div>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">{selectedNode.data.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Description</label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedNode.data.description || 'No description available'}
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Type</label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedNode.data.nodeType || 'custom'}
                    </p>
                  </div>
                  
                  {selectedNode.data.inputs && selectedNode.data.inputs.length > 0 && (
                    <div>
                      <label className="text-sm font-medium">Inputs</label>
                      <div className="mt-2 space-y-1">
                        {selectedNode.data.inputs.map((input: any) => (
                          <div key={input.id} className="text-sm">
                            <span className="font-medium">{input.name}</span>
                            <span className="text-muted-foreground ml-2">({input.type})</span>
                            {input.required && <span className="text-red-500 ml-1">*</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedNode.data.outputs && selectedNode.data.outputs.length > 0 && (
                    <div>
                      <label className="text-sm font-medium">Outputs</label>
                      <div className="mt-2 space-y-1">
                        {selectedNode.data.outputs.map((output: any) => (
                          <div key={output.id} className="text-sm">
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