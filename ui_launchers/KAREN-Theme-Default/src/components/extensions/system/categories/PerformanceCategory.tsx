"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { Zap, Cpu, Database, Network, TrendingUp, Settings } from "lucide-react";

export interface PerformanceExtension {
  id: string;
  name: string;
  displayName?: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  enabled: boolean;
  impact: 'high' | 'medium' | 'low';
  metrics: {
    cpuUsage?: number;
    memoryUsage?: number;
    responseTime?: number;
    throughput?: number;
  };
  optimization?: string;
}

export interface PerformanceCategoryProps {
  refreshInterval?: number;
  onConfigure?: (id: string) => void;
}

const mockPerformanceExtensions: PerformanceExtension[] = [
  {
    id: 'cache-redis',
    name: 'redis-cache',
    displayName: 'Redis Cache',
    description: 'High-performance in-memory caching for faster data access',
    status: 'active',
    enabled: true,
    impact: 'high',
    metrics: {
      cpuUsage: 12,
      memoryUsage: 256,
      responseTime: 2,
      throughput: 50000,
    },
    optimization: 'Reduces database queries by 85%',
  },
  {
    id: 'cdn-integration',
    name: 'cdn',
    displayName: 'CDN Integration',
    description: 'Content delivery network for faster static asset delivery',
    status: 'active',
    enabled: true,
    impact: 'high',
    metrics: {
      cpuUsage: 5,
      memoryUsage: 64,
      responseTime: 50,
      throughput: 100000,
    },
    optimization: 'Reduces page load time by 60%',
  },
  {
    id: 'query-optimizer',
    name: 'query-optimizer',
    displayName: 'Database Query Optimizer',
    description: 'Optimizes database queries for better performance',
    status: 'active',
    enabled: true,
    impact: 'high',
    metrics: {
      cpuUsage: 8,
      memoryUsage: 128,
      responseTime: 15,
      throughput: 10000,
    },
    optimization: 'Reduces query execution time by 70%',
  },
  {
    id: 'compression',
    name: 'compression',
    displayName: 'Response Compression',
    description: 'Gzip/Brotli compression for reduced bandwidth usage',
    status: 'active',
    enabled: true,
    impact: 'medium',
    metrics: {
      cpuUsage: 3,
      memoryUsage: 32,
      responseTime: 5,
      throughput: 75000,
    },
    optimization: 'Reduces response size by 75%',
  },
  {
    id: 'load-balancer',
    name: 'load-balancer',
    displayName: 'Load Balancer',
    description: 'Distributes traffic across multiple servers',
    status: 'active',
    enabled: true,
    impact: 'high',
    metrics: {
      cpuUsage: 10,
      memoryUsage: 192,
      responseTime: 1,
      throughput: 200000,
    },
    optimization: 'Improves system capacity by 400%',
  },
  {
    id: 'image-optimizer',
    name: 'image-optimizer',
    displayName: 'Image Optimizer',
    description: 'Automatic image optimization and format conversion',
    status: 'inactive',
    enabled: false,
    impact: 'medium',
    metrics: {
      cpuUsage: 0,
      memoryUsage: 0,
      responseTime: 0,
      throughput: 0,
    },
    optimization: 'Reduces image size by 60%',
  },
];

const impactConfig = {
  high: {
    label: 'High Impact',
    color: 'text-green-500',
    bgColor: 'bg-green-500',
  },
  medium: {
    label: 'Medium Impact',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500',
  },
  low: {
    label: 'Low Impact',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500',
  },
};

export default function PerformanceCategory({
  refreshInterval = 10000,
  onConfigure,
}: PerformanceCategoryProps) {
  const [extensions, setExtensions] = useState<PerformanceExtension[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadExtensions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/extensions/category/performance');
      if (response.ok) {
        const data = await response.json();
        setExtensions(data);
      } else {
        // Fallback to mock data
        setExtensions(mockPerformanceExtensions);
      }
    } catch (error) {
      console.error('Failed to load performance extensions:', error);
      setExtensions(mockPerformanceExtensions);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadExtensions();
    const interval = setInterval(loadExtensions, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const stats = {
    total: extensions.length,
    active: extensions.filter((ext) => ext.status === 'active').length,
    avgCpu: Math.round(
      extensions.reduce((sum, ext) => sum + (ext.metrics.cpuUsage || 0), 0) / extensions.length
    ),
    avgMemory: Math.round(
      extensions.reduce((sum, ext) => sum + (ext.metrics.memoryUsage || 0), 0) / extensions.length
    ),
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Extensions</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <Zap className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active</p>
                <p className="text-2xl font-bold text-green-500">{stats.active}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg CPU Usage</p>
                <p className="text-2xl font-bold">{stats.avgCpu}%</p>
              </div>
              <Cpu className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg Memory</p>
                <p className="text-2xl font-bold">{stats.avgMemory} MB</p>
              </div>
              <Database className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Extensions List */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Extensions</CardTitle>
          <CardDescription>
            Manage caching, optimization, and performance-enhancing extensions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-4">
              {extensions.map((extension) => {
                const impact = impactConfig[extension.impact];

                return (
                  <Card key={extension.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">
                              {extension.displayName || extension.name}
                            </h3>
                            <Badge
                              variant={extension.status === 'active' ? 'default' : 'secondary'}
                            >
                              {extension.status}
                            </Badge>
                            <div className={`flex items-center gap-1 ${impact.color}`}>
                              <Zap className="h-4 w-4" />
                              <span className="text-xs font-medium">{impact.label}</span>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground">
                            {extension.description}
                          </p>

                          {extension.optimization && (
                            <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-2 rounded">
                              <TrendingUp className="h-3 w-3" />
                              {extension.optimization}
                            </div>
                          )}

                          {/* Metrics */}
                          {extension.status === 'active' && (
                            <div className="grid gap-3 md:grid-cols-2">
                              {extension.metrics.cpuUsage !== undefined && (
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <span className="flex items-center gap-1">
                                      <Cpu className="h-3 w-3" />
                                      CPU Usage
                                    </span>
                                    <span className="font-medium">
                                      {extension.metrics.cpuUsage}%
                                    </span>
                                  </div>
                                  <Progress value={extension.metrics.cpuUsage} />
                                </div>
                              )}

                              {extension.metrics.memoryUsage !== undefined && (
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <span className="flex items-center gap-1">
                                      <Database className="h-3 w-3" />
                                      Memory
                                    </span>
                                    <span className="font-medium">
                                      {extension.metrics.memoryUsage} MB
                                    </span>
                                  </div>
                                  <Progress
                                    value={(extension.metrics.memoryUsage / 512) * 100}
                                  />
                                </div>
                              )}

                              {extension.metrics.responseTime !== undefined && (
                                <div className="text-xs">
                                  <span className="flex items-center gap-1">
                                    <Network className="h-3 w-3" />
                                    Response Time: {extension.metrics.responseTime}ms
                                  </span>
                                </div>
                              )}

                              {extension.metrics.throughput !== undefined && (
                                <div className="text-xs">
                                  <span className="flex items-center gap-1">
                                    <TrendingUp className="h-3 w-3" />
                                    Throughput: {extension.metrics.throughput.toLocaleString()}{' '}
                                    req/s
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        {onConfigure && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onConfigure(extension.id)}
                          >
                            <Settings className="h-4 w-4 mr-1" />
                            Configure
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

export { PerformanceCategory };
export type { PerformanceCategoryProps, PerformanceExtension };
