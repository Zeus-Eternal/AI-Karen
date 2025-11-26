'use client';

import React, { useState } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/ModernHeader';
import { MetricCard } from '@/components/ui/metric-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Brain,
  Database,
  Search,
  TrendingUp,
  Clock,
  Trash2,
  Eye,
  Download,
} from 'lucide-react';
import { AnimatedNumber } from '@/components/ui/animated-number';
import { Sparkline } from '@/components/ui/sparkline';
import { useAuth } from '@/hooks/use-auth';
import MemoryGrid from '@/components/memory/MemoryGrid';

interface MemoryEntry {
  id: string;
  content: string;
  embedding: number[];
  metadata: {
    timestamp: Date;
    source: string;
    tags: string[];
    accessCount: number;
  };
  similarity?: number;
}

export default function MemoryLabPage() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMemory, setSelectedMemory] = useState<MemoryEntry | null>(null);

  // Mock data for stats (these would come from an API in production)
  const memoryStats = {
    totalVectors: 89234,
    totalSize: 2.4, // GB
    collections: 12,
    avgSearchLatency: 45, // ms
  };

  const sparklineData = [30, 35, 32, 40, 38, 45, 48, 46, 50, 52];

  return (
    <div className="min-h-screen bg-background">
      <Sidebar/>
      <Header />

      <main className="ml-64 mt-16 p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-600">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Memory Lab</h1>
                <p className="text-muted-foreground">
                  Explore, analyze, and manage Kari&rsquo;s memory systems
                </p>
              </div>
            </div>
          </div>

          {/* Memory Statistics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total Vectors"
              value={<AnimatedNumber value={memoryStats.totalVectors} />}
              subtitle="Stored embeddings"
              icon={Database}
              variant="primary"
              trend={{
                value: 5.2,
                isPositive: true,
              }}
            />
            <MetricCard
              title="Storage Size"
              value={`${memoryStats.totalSize}GB`}
              subtitle="Vector storage"
              icon={TrendingUp}
              variant="default"
            />
            <MetricCard
              title="Collections"
              value={<AnimatedNumber value={memoryStats.collections} />}
              subtitle="Active namespaces"
              icon={Brain}
              variant="success"
            />
            <MetricCard
              title="Search Latency"
              value={`${memoryStats.avgSearchLatency}ms`}
              subtitle="Average p95"
              icon={Clock}
              variant="default"
            />
          </div>

          {/* Memory Interface */}
          <Card>
            <CardHeader>
              <CardTitle>Memory Browser</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="search" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="search">Semantic Search</TabsTrigger>
                  <TabsTrigger value="browse">Browse All</TabsTrigger>
                  <TabsTrigger value="analytics">Analytics</TabsTrigger>
                  <TabsTrigger value="visualization">Visualization</TabsTrigger>
                </TabsList>

                {/* Semantic Search Tab */}
                <TabsContent value="search" className="space-y-4">
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        placeholder="Search memories semantically..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                    <Button>Search</Button>
                  </div>

                  <div className="h-[500px]">
                    {user && (
                      <MemoryGrid
                        userId={user.userId}
                        tenantId={user.tenantId}
                        onMemorySelect={(memory) => {
                          // Convert MemoryGridRow to MemoryEntry format for compatibility
                          setSelectedMemory({
                            id: memory.id,
                            content: memory.content,
                            embedding: [],
                            metadata: {
                              timestamp: new Date(memory.timestamp),
                              source: memory.semantic_cluster,
                              tags: [],
                              accessCount: 0,
                            },
                            similarity: memory.relevance_score,
                          });
                        }}
                      />
                    )}
                  </div>
                </TabsContent>

                {/* Analytics Tab */}
                <TabsContent value="analytics" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">
                          Search Performance
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">
                              Average Latency
                            </span>
                            <span className="font-semibold">45ms</span>
                          </div>
                          <Sparkline
                            data={sparklineData}
                            width={300}
                            height={60}
                            strokeColor="rgb(59, 130, 246)"
                            fillColor="rgb(59, 130, 246)"
                            showArea
                          />
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">
                          Most Accessed Memories
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <p className="text-sm text-muted-foreground">
                            Memory analytics will be displayed here when data is available.
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* Visualization Tab */}
                <TabsContent value="visualization" className="space-y-4">
                  <Card className="flex items-center justify-center h-[500px]">
                    <div className="text-center text-muted-foreground">
                      <Brain className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-medium">Vector Space Visualization</p>
                      <p className="text-sm mt-2">
                        3D visualization of memory embeddings coming soon
                      </p>
                      <p className="text-xs mt-1">
                        Will use Three.js for interactive 3D exploration
                      </p>
                    </div>
                  </Card>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Memory Details Panel (if selected) */}
          {selectedMemory && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Memory Details</span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                    <Button size="sm" variant="outline">
                      <Download className="h-4 w-4 mr-1" />
                      Export
                    </Button>
                    <Button size="sm" variant="destructive">
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium mb-2">Content</h4>
                    <p className="text-sm text-muted-foreground">
                      {selectedMemory.content}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-2">Metadata</h4>
                    <dl className="grid grid-cols-2 gap-2 text-sm">
                      <dt className="text-muted-foreground">Source:</dt>
                      <dd>{selectedMemory.metadata.source}</dd>
                      <dt className="text-muted-foreground">Created:</dt>
                      <dd>
                        {selectedMemory.metadata.timestamp.toLocaleString()}
                      </dd>
                      <dt className="text-muted-foreground">Access Count:</dt>
                      <dd>{selectedMemory.metadata.accessCount}</dd>
                      <dt className="text-muted-foreground">Embedding Dim:</dt>
                      <dd>{selectedMemory.embedding.length}</dd>
                    </dl>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </div>
  );
}
