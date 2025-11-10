"use client";

import React, { useState, useMemo, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, Box, Cpu, Database, GitBranch, FileOutput, Puzzle, Rocket } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

import { NodePort, NodeTemplate } from '@/types/workflows';

export interface NodeLibraryProps {
  readOnly?: boolean;
}

const defaultNodeTemplates: NodeTemplate[] = [
  {
    id: 'input-text',
    name: 'Text Input',
    description: 'Captures user provided text or contextual data.',
    category: 'input',
    icon: 'Box',
    inputs: [],
    outputs: [createPort('text-output', 'Text Output', 'string')],
    config: {
      schema: {
        placeholder: { type: 'string', description: 'UI placeholder for the input field.' },
      },
      defaults: {
        placeholder: 'Enter text...'
      },
    },
  },
  {
    id: 'llm-prompt',
    name: 'LLM Prompt',
    description: 'Sends structured prompts to the configured language model.',
    category: 'ai',
    icon: 'Cpu',
    inputs: [
      createPort('prompt', 'Prompt', 'string', true, 'Prompt template or raw text to send to the model.'),
      createPort('context', 'Context', 'object'),
    ],
    outputs: [
      createPort('response', 'Response', 'string'),
      createPort('tokens', 'Token Usage', 'object'),
    ],
    config: {
      schema: {
        model: { type: 'string', enum: ['gpt-4', 'gpt-3.5', 'karen-pro'] },
        temperature: { type: 'number', minimum: 0, maximum: 1 },
      },
      defaults: {
        model: 'gpt-4',
        temperature: 0.2,
      },
    },
  },
  {
    id: 'branch-control',
    name: 'Branch Control',
    description: 'Evaluates a condition and routes execution accordingly.',
    category: 'control',
    icon: 'GitBranch',
    inputs: [createPort('condition', 'Condition', 'boolean', true)],
    outputs: [
      createPort('on-true', 'On True', 'any'),
      createPort('on-false', 'On False', 'any'),
    ],
    config: {
      schema: {
        evaluation: { type: 'string', description: 'Expression evaluated against runtime variables.' },
      },
      defaults: {
        evaluation: '{{input.value}} === true',
      },
    },
  },
  {
    id: 'json-output',
    name: 'JSON Output',
    description: 'Formats and emits workflow results as structured JSON.',
    category: 'output',
    icon: 'FileOutput',
    inputs: [createPort('payload', 'Payload', 'object', true)],
    outputs: [],
    config: {
      schema: {
        pretty: { type: 'boolean', description: 'Pretty print the JSON output.' },
      },
      defaults: {
        pretty: true,
      },
    },
  },
  {
    id: 'data-retrieval',
    name: 'Data Retrieval',
    description: 'Fetches records from an external data source.',
    category: 'integration',
    icon: 'Database',
    inputs: [
      createPort('query', 'Query', 'string', true),
      createPort('parameters', 'Parameters', 'object'),
    ],
    outputs: [createPort('records', 'Records', 'array')],
    config: {
      schema: {
        provider: { type: 'string', enum: ['postgres', 'mysql', 'elastic'] },
      },
      defaults: {
        provider: 'postgres',
      },
    },
  },
  {
    id: 'webhook-trigger',
    name: 'Webhook Trigger',
    description: 'Starts workflows from inbound webhook calls.',
    category: 'input',
    icon: 'Rocket',
    inputs: [],
    outputs: [createPort('event', 'Event Payload', 'object')],
    config: {
      schema: {
        method: { type: 'string', enum: ['GET', 'POST', 'PUT'] },
        path: { type: 'string' },
      },
      defaults: {
        method: 'POST',
        path: '/webhooks/new-event',
      },
    },
  },
];

const iconLibrary = {
  Box,
  Cpu,
  Database,
  GitBranch,
  FileOutput,
  Puzzle,
  Rocket,
} satisfies Record<string, LucideIcon>;

type IconName = keyof typeof iconLibrary;

const categoryIcons: Partial<Record<NodeTemplate['category'], LucideIcon>> = {
  input: Box,
  ai: Cpu,
  processing: Puzzle,
  control: GitBranch,
  output: FileOutput,
  integration: Database,
};

function createPort(id: string, name: string, type: NodePort['type'], required = false, description?: string): NodePort {
  return {
    id,
    name,
    type,
    required,
    description,
  };
}

export function NodeLibrary({ readOnly = false }: NodeLibraryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | NodeTemplate['category']>('all');

  // Categories derived from node templates
  const categories = useMemo(() => {
    const cats = Array.from(new Set(defaultNodeTemplates.map(node => node.category)));
    return ['all', ...cats] as const;
  }, []);

  // Filter nodes based on search term and selected category
  const filteredNodes = useMemo(() => {
    return defaultNodeTemplates.filter(node => {
      const matchesSearch = node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           node.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || node.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, selectedCategory]);

  const handleCategoryChange = useCallback((value: string) => {
    if (value === 'all') {
      setSelectedCategory('all');
      return;
    }

    if (defaultNodeTemplates.some(node => node.category === value)) {
      setSelectedCategory(value as NodeTemplate['category']);
    }
  }, []);

  const resolveIcon = useCallback(
    (icon: string, category: NodeTemplate['category']): LucideIcon => {
      if ((icon as IconName) in iconLibrary) {
        return iconLibrary[icon as IconName];
      }
      return categoryIcons[category] ?? Puzzle;
    },
    []
  );

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
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          placeholder="Search nodes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={handleCategoryChange}>
        <TabsList className="grid w-full grid-cols-3">
          {categories.map(category => (
            <TabsTrigger key={category} value={category} className="text-xs sm:text-sm md:text-base">
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Node List */}
      <ScrollArea className="h-[600px]">
        <div className="space-y-2">
          {filteredNodes.map((node) => {
            const IconComponent = resolveIcon(node.icon, node.category);
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
                  <CardContent className="p-3 sm:p-4 md:p-6">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <IconComponent className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-medium text-sm truncate md:text-base lg:text-lg">{node.name}</h4>
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                            {node.category}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2 mb-2 sm:text-sm md:text-base">
                          {node.description}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
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
              <p className="text-sm md:text-base lg:text-lg">No nodes found matching your search.</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
