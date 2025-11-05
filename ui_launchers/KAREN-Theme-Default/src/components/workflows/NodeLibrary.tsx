"use client";

import React, { useState, useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search } from 'lucide-react';

interface NodeLibraryProps {
  readOnly?: boolean;
}

interface NodeTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  inputs: Array<any>;
  outputs: Array<any>;
}

const nodeTemplates: NodeTemplate[] = [
  // Example Node Templates
  { id: '1', name: 'Input Node', description: 'Handles input data', category: 'input', inputs: [], outputs: [] },
  { id: '2', name: 'AI Model', description: 'AI processing node', category: 'ai', inputs: [], outputs: [] },
  { id: '3', name: 'Output Node', description: 'Handles output data', category: 'output', inputs: [], outputs: [] },
  { id: '4', name: 'Control Node', description: 'For control logic', category: 'control', inputs: [], outputs: [] },
  // Add more node templates as necessary
];

const categoryIcons = {
  input: 'InputIcon',
  ai: 'AiIcon',
  output: 'OutputIcon',
  control: 'ControlIcon',
  integration: 'IntegrationIcon',
  // Add additional icons for more categories
};

export function NodeLibrary({ readOnly = false }: NodeLibraryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Categories derived from node templates
  const categories = useMemo(() => {
    const cats = Array.from(new Set(nodeTemplates.map(node => node.category)));
    return ['all', ...cats];
  }, []);

  // Filter nodes based on search term and selected category
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
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
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
            const IconComponent = categoryIcons[node.category as keyof typeof categoryIcons] || 'DefaultIcon';
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
