"use client";

import * as React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, Square, Brain, Database, Plug, GitBranch, RotateCcw, Settings, CheckCircle, AlertCircle } from 'lucide-react';

export interface WorkflowNodeData {
  label: string;
  description?: string;
  nodeType: string;
  config: Record<string, any>;
  inputs?: Array<{
    id: string;
    name: string;
    type: string;
    required?: boolean;
  }>;
  outputs?: Array<{
    id: string;
    name: string;
    type: string;
  }>;
  status?: 'idle' | 'running' | 'completed' | 'error';
  error?: string;
}

const nodeIcons = {
  input: Play,
  output: Square,
  llm: Brain,
  memory: Database,
  plugin: Plug,
  condition: GitBranch,
  loop: RotateCcw,
  custom: Settings,
};

const nodeColors = {
  input: 'bg-green-50 border-green-200 text-green-800',
  output: 'bg-blue-50 border-blue-200 text-blue-800',
  llm: 'bg-purple-50 border-purple-200 text-purple-800',
  memory: 'bg-orange-50 border-orange-200 text-orange-800',
  plugin: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  condition: 'bg-pink-50 border-pink-200 text-pink-800',
  loop: 'bg-indigo-50 border-indigo-200 text-indigo-800',
  custom: 'bg-gray-50 border-gray-200 text-gray-800',
};

const statusColors = {
  idle: 'bg-gray-100 text-gray-600',
  running: 'bg-blue-100 text-blue-600',
  completed: 'bg-green-100 text-green-600',
  error: 'bg-red-100 text-red-600',
};

export const WorkflowNodeComponent = React.memo<NodeProps<WorkflowNodeData>>(({ data, selected }) => {
  const IconComponent = nodeIcons[data.nodeType as keyof typeof nodeIcons] || nodeIcons.custom;
  const nodeColorClass = nodeColors[data.nodeType as keyof typeof nodeColors] || nodeColors.custom;
  
  return (
    <Card 
      className={`
        min-w-[200px] max-w-[300px] transition-all duration-200
        ${selected ? 'ring-2 ring-blue-500 shadow-lg' : 'shadow-sm'}
        ${nodeColorClass}
      `}
    >
      {/* Input Handles */}
      {data.inputs?.map((input, index) => (
        <Handle
          key={input.id}
          type="target"
          position={Position.Left}
          id={input.id}
          style={{
            top: `${((index + 1) / (data.inputs!.length + 1)) * 100}%`,
            background: input.required ? '#ef4444' : '#6b7280',
          }}
          className="w-3 h-3 "
        />
      ))}

      <CardContent className="p-3 sm:p-4 md:p-6">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <IconComponent className="h-5 w-5 " />
          </div>
          
          <div className="flex-1 min-w-0 ">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-medium text-sm truncate md:text-base lg:text-lg">{data.label}</h4>
              {data.status && (
                <Badge 
                  variant="secondary" 
                  className={`text-xs ${statusColors[data.status]}`}
                >
                  {data.status === 'running' && <div className="w-2 h-2 bg-current rounded-full animate-pulse mr-1 " />}
                  {data.status === 'completed' && <CheckCircle className="w-3 h-3 mr-1 " />}
                  {data.status === 'error' && <AlertCircle className="w-3 h-3 mr-1 " />}
                  {data.status}
                </Badge>
              )}
            </div>
            
            {data.description && (
              <p className="text-xs text-muted-foreground line-clamp-2 mb-2 sm:text-sm md:text-base">
                {data.description}
              </p>
            )}
            
            {data.error && (
              <div className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200 mb-2 sm:text-sm md:text-base">
                {data.error}
              </div>
            )}
            
            <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
              <span>{data.nodeType}</span>
              {(data.inputs?.length || 0) > 0 && (
                <span>{data.inputs?.length} input{data.inputs?.length !== 1 ? 's' : ''}</span>
              )}
            </div>
          </div>
        </div>
      </CardContent>

      {/* Output Handles */}
      {data.outputs?.map((output, index) => (
        <Handle
          key={output.id}
          type="source"
          position={Position.Right}
          id={output.id}
          style={{
            top: `${((index + 1) / (data.outputs!.length + 1)) * 100}%`,
            background: '#6b7280',
          }}
          className="w-3 h-3 "
        />
      ))}
    </Card>
  );
});

WorkflowNodeComponent.displayName = 'WorkflowNodeComponent';