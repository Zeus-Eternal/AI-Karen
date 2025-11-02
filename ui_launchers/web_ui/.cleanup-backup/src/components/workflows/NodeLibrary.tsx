'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Brain, 
  Database, 
  Plug, 
  GitBranch, 
  RotateCcw, 
  Play, 
  Square, 
  Settings,
  Search,
  FileInput,
  FileOutput,
  Zap
} from 'lucide-react';

import { NodeTemplate } from '@/types/workflows';

const nodeTemplates: NodeTemplate[] = [
  // Input Nodes
  {
    id: 'text-input',
    name: 'Text Input',
    category: 'input',
    description: 'Accepts text input from user or external source',
    icon: 'FileInput',
    inputs: [],
    outputs: [
      { id: 'text', name: 'Text', type: 'string', description: 'The input text' }
    ],
    config: {
      schema: {
        placeholder: { type: 'string', default: 'Enter text...' },
        multiline: { type: 'boolean', default: false },
        required: { type: 'boolean', default: true }
      },
      defaults: {
        placeholder: 'Enter text...',
        multiline: false,
        required: true
      }
    }
  },
  {
    id: 'file-input',
    name: 'File Input',
    category: 'input',
    description: 'Accepts file uploads and processes file content',
    icon: 'FileInput',
    inputs: [],
    outputs: [
      { id: 'content', name: 'Content', type: 'string', description: 'File content' },
      { id: 'metadata', name: 'Metadata', type: 'object', description: 'File metadata' }
    ],
    config: {
      schema: {
        acceptedTypes: { type: 'array', default: ['text/*', 'application/pdf'] },
        maxSize: { type: 'number', default: 10485760 }
      },
      defaults: {
        acceptedTypes: ['text/*', 'application/pdf'],
        maxSize: 10485760
      }
    }
  },

  // Processing Nodes
  {
    id: 'llm-chat',
    name: 'LLM Chat',
    category: 'ai',
    description: 'Processes text using a large language model',
    icon: 'Brain',
    inputs: [
      { id: 'prompt', name: 'Prompt', type: 'string', required: true, description: 'The prompt to send to the LLM' },
      { id: 'context', name: 'Context', type: 'string', description: 'Additional context for the LLM' }
    ],
    outputs: [
      { id: 'response', name: 'Response', type: 'string', description: 'LLM response' },
      { id: 'metadata', name: 'Metadata', type: 'object', description: 'Response metadata' }
    ],
    config: {
      schema: {
        model: { type: 'string', default: 'gpt-3.5-turbo' },
        temperature: { type: 'number', default: 0.7, min: 0, max: 2 },
        maxTokens: { type: 'number', default: 1000 },
        systemPrompt: { type: 'string', default: '' }
      },
      defaults: {
        model: 'gpt-3.5-turbo',
        temperature: 0.7,
        maxTokens: 1000,
        systemPrompt: ''
      }
    }
  },
  {
    id: 'memory-search',
    name: 'Memory Search',
    category: 'ai',
    description: 'Searches through memory/knowledge base',
    icon: 'Database',
    inputs: [
      { id: 'query', name: 'Query', type: 'string', required: true, description: 'Search query' },
      { id: 'filters', name: 'Filters', type: 'object', description: 'Search filters' }
    ],
    outputs: [
      { id: 'results', name: 'Results', type: 'array', description: 'Search results' },
      { id: 'count', name: 'Count', type: 'number', description: 'Number of results' }
    ],
    config: {
      schema: {
        limit: { type: 'number', default: 10 },
        threshold: { type: 'number', default: 0.7 },
        includeMetadata: { type: 'boolean', default: true }
      },
      defaults: {
        limit: 10,
        threshold: 0.7,
        includeMetadata: true
      }
    }
  },
  {
    id: 'plugin-executor',
    name: 'Plugin Executor',
    category: 'integration',
    description: 'Executes a plugin or external tool',
    icon: 'Plug',
    inputs: [
      { id: 'input', name: 'Input', type: 'any', required: true, description: 'Plugin input data' },
      { id: 'config', name: 'Config', type: 'object', description: 'Plugin configuration' }
    ],
    outputs: [
      { id: 'output', name: 'Output', type: 'any', description: 'Plugin output' },
      { id: 'status', name: 'Status', type: 'string', description: 'Execution status' }
    ],
    config: {
      schema: {
        pluginId: { type: 'string', required: true },
        timeout: { type: 'number', default: 30000 },
        retries: { type: 'number', default: 3 }
      },
      defaults: {
        pluginId: '',
        timeout: 30000,
        retries: 3
      }
    }
  },

  // Control Flow Nodes
  {
    id: 'condition',
    name: 'Condition',
    category: 'control',
    description: 'Conditional branching based on input evaluation',
    icon: 'GitBranch',
    inputs: [
      { id: 'input', name: 'Input', type: 'any', required: true, description: 'Value to evaluate' },
      { id: 'condition', name: 'Condition', type: 'string', description: 'Condition expression' }
    ],
    outputs: [
      { id: 'true', name: 'True', type: 'any', description: 'Output when condition is true' },
      { id: 'false', name: 'False', type: 'any', description: 'Output when condition is false' }
    ],
    config: {
      schema: {
        expression: { type: 'string', required: true },
        operator: { type: 'string', default: 'equals', enum: ['equals', 'contains', 'greater', 'less'] }
      },
      defaults: {
        expression: '',
        operator: 'equals'
      }
    }
  },
  {
    id: 'loop',
    name: 'Loop',
    category: 'control',
    description: 'Iterates over a collection or repeats until condition',
    icon: 'RotateCcw',
    inputs: [
      { id: 'collection', name: 'Collection', type: 'array', description: 'Items to iterate over' },
      { id: 'condition', name: 'Condition', type: 'string', description: 'Loop condition' }
    ],
    outputs: [
      { id: 'item', name: 'Current Item', type: 'any', description: 'Current iteration item' },
      { id: 'index', name: 'Index', type: 'number', description: 'Current iteration index' },
      { id: 'results', name: 'Results', type: 'array', description: 'Collected results' }
    ],
    config: {
      schema: {
        maxIterations: { type: 'number', default: 100 },
        collectResults: { type: 'boolean', default: true }
      },
      defaults: {
        maxIterations: 100,
        collectResults: true
      }
    }
  },

  // Output Nodes
  {
    id: 'text-output',
    name: 'Text Output',
    category: 'output',
    description: 'Displays or returns text output',
    icon: 'FileOutput',
    inputs: [
      { id: 'text', name: 'Text', type: 'string', required: true, description: 'Text to output' },
      { id: 'format', name: 'Format', type: 'string', description: 'Output format' }
    ],
    outputs: [],
    config: {
      schema: {
        format: { type: 'string', default: 'plain', enum: ['plain', 'markdown', 'html'] },
        destination: { type: 'string', default: 'display', enum: ['display', 'file', 'api'] }
      },
      defaults: {
        format: 'plain',
        destination: 'display'
      }
    }
  },
  {
    id: 'webhook-output',
    name: 'Webhook Output',
    category: 'output',
    description: 'Sends data to an external webhook',
    icon: 'Zap',
    inputs: [
      { id: 'data', name: 'Data', type: 'any', required: true, description: 'Data to send' },
      { id: 'headers', name: 'Headers', type: 'object', description: 'HTTP headers' }
    ],
    outputs: [
      { id: 'response', name: 'Response', type: 'object', description: 'Webhook response' },
      { id: 'status', name: 'Status', type: 'number', description: 'HTTP status code' }
    ],
    config: {
      schema: {
        url: { type: 'string', required: true },
        method: { type: 'string', default: 'POST', enum: ['GET', 'POST', 'PUT', 'DELETE'] },
        timeout: { type: 'number', default: 10000 }
      },
      defaults: {
        url: '',
        method: 'POST',
        timeout: 10000
      }
    }
  }
];

const categoryIcons = {
  input: FileInput,
  processing: Settings,
  output: FileOutput,
  control: GitBranch,
  ai: Brain,
  integration: Plug,
};

interface NodeLibraryProps {
  readOnly?: boolean;
}

export function NodeLibrary({ readOnly = false }: NodeLibraryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = useMemo(() => {
    const cats = Array.from(new Set(nodeTemplates.map(node => node.category)));
    return ['all', ...cats];
  }, []);

  const filteredNodes = useMemo(() => {
    return nodeTemplates.filter(node => {
      const matchesSearch = node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           node.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || node.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, selectedCategory]);

  const onDragStart = (event: React.DragEvent, nodeTemplate: NodeTemplate) => {
    if (readOnly) {
      event.preventDefault();
      return;
    }
    
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeTemplate));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search nodes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="all" className="text-xs">All</TabsTrigger>
          <TabsTrigger value="input" className="text-xs">Input</TabsTrigger>
          <TabsTrigger value="ai" className="text-xs">AI</TabsTrigger>
        </TabsList>
        <TabsList className="grid w-full grid-cols-3 mt-1">
          <TabsTrigger value="control" className="text-xs">Control</TabsTrigger>
          <TabsTrigger value="integration" className="text-xs">Tools</TabsTrigger>
          <TabsTrigger value="output" className="text-xs">Output</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Node List */}
      <ScrollArea className="h-[600px]">
        <div className="space-y-2">
          {filteredNodes.map((node) => {
            const IconComponent = categoryIcons[node.category as keyof typeof categoryIcons] || Settings;
            
            return (
              <div
                key={node.id}
                draggable={!readOnly}
                onDragStart={(e) => onDragStart(e, node)}
              >
                <Card
                  className={`
                    cursor-pointer transition-all duration-200 hover:shadow-md
                    ${readOnly ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary'}
                  `}
                >
                <CardContent className="p-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0">
                      <IconComponent className="h-4 w-4 text-muted-foreground" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium text-sm truncate">{node.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          {node.category}
                        </Badge>
                      </div>
                      
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {node.description}
                      </p>
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{node.inputs.length} in</span>
                        <span>{node.outputs.length} out</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              </div>
            );
          })}
          
          {filteredNodes.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No nodes found matching your search.</p>
            </div>
          )}
        </div>
      </ScrollArea>
      
      {!readOnly && (
        <div className="text-xs text-muted-foreground text-center p-2 border-t">
          Drag nodes to the canvas to build your workflow
        </div>
      )}
    </div>
  );
}