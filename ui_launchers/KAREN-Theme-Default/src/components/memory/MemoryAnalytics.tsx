/**
 * Memory Analytics Dashboard Component
 * Displays comprehensive vector store statistics and performance metrics
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, TrendingUp, TrendingDown, Activity, Database, Clock, Zap } from 'lucide-react';
import { getMemoryService } from '@/services/memoryService';
import type { MemoryAnalytics as MemoryAnalyticsData, MemoryAnalyticsProps } from '@/types/memory';
import { safeDebug } from '@/lib/safe-console';

// Lazy load charts for better performance
const AgCharts = dynamic(() => import('ag-charts-react').then(m => m.AgCharts), { ssr: false });
import type { AgChartOptions } from 'ag-charts-community';

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'orange' | 'red' | 'purple';
  loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ 
  title, 
  value, 
  change, 
  changeLabel, 
  icon, 
  color = 'blue',
  loading = false 
}) => {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    orange: 'text-orange-600 bg-orange-50',
    red: 'text-red-600 bg-red-50',
    purple: 'text-purple-600 bg-purple-50'
  };

  return (
    <Card className="p-6 sm:p-4 md:p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">{title}</p>
          <div className="flex items-center mt-2">
            {loading ? (
              <div className="h-8 w-24 bg-gray-200 animate-pulse rounded "></div>
            ) : (
              <p className="text-2xl font-bold text-gray-900">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </p>
            )}
            {change !== undefined && !loading && (
              <div className={`ml-2 flex items-center text-sm ${
                change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {change >= 0 ? <TrendingUp className="w-4 h-4 " /> : <TrendingDown className="w-4 h-4 " />}
                <span className="ml-1">
                  {Math.abs(change)}% {changeLabel || (change >= 0 ? 'increase' : 'decrease')}
                </span>
              </div>
            )}
          </div>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </Card>
  );
};

export const MemoryAnalytics: React.FC<MemoryAnalyticsProps> = ({
  userId,
  tenantId,
  refreshInterval = 30000, // 30 seconds
  height = 800,
  onError
}) => {
  const [analytics, setAnalytics] = useState<MemoryAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const memoryService = useMemo(() => getMemoryService(), []);

  // Fetch analytics data
  const fetchAnalytics = useCallback(async () => {
    try {
      setError(null);

      safeDebug('MemoryAnalytics: fetching analytics', {
        userId,
        tenantId,
      });

      // Get basic memory stats
      const stats = await memoryService.getMemoryStats(userId);
      
      // Simulate comprehensive analytics data (in real implementation, this would come from backend)
      const mockAnalytics: MemoryAnalyticsData = {
        vectorStore: {
          totalEmbeddings: stats.totalMemories,
          storageSize: stats.totalMemories * 1024, // Mock storage size
          averageLatency: 45 + Math.random() * 20, // Mock latency
          searchAccuracy: 0.85 + Math.random() * 0.1,
          memoryDecay: [
            { timeRange: '1d', retentionRate: 0.95, accessFrequency: 0.8, forgettingCurve: 0.05 },
            { timeRange: '7d', retentionRate: 0.88, accessFrequency: 0.6, forgettingCurve: 0.12 },
            { timeRange: '30d', retentionRate: 0.75, accessFrequency: 0.4, forgettingCurve: 0.25 },
            { timeRange: '90d', retentionRate: 0.60, accessFrequency: 0.2, forgettingCurve: 0.40 }
          ],
          embeddingDimensions: 1536,
          indexType: 'HNSW',
          lastUpdated: new Date()
        },
        usage: {
          totalMemories: stats.totalMemories,
          memoriesByType: stats.memoriesByTag,
          memoriesByCluster: {
            'technical': Math.floor(stats.totalMemories * 0.3),
            'personal': Math.floor(stats.totalMemories * 0.25),
            'work': Math.floor(stats.totalMemories * 0.2),
            'general': Math.floor(stats.totalMemories * 0.25)
          },
          memoriesByAge: [
            { range: '< 1 day', count: Math.floor(stats.totalMemories * 0.1) },
            { range: '1-7 days', count: Math.floor(stats.totalMemories * 0.2) },
            { range: '1-4 weeks', count: Math.floor(stats.totalMemories * 0.3) },
            { range: '1-3 months', count: Math.floor(stats.totalMemories * 0.25) },
            { range: '> 3 months', count: Math.floor(stats.totalMemories * 0.15) }
          ],
          storageBreakdown: {
            embeddings: Math.floor(stats.totalMemories * 1024 * 0.7),
            metadata: Math.floor(stats.totalMemories * 1024 * 0.15),
            content: Math.floor(stats.totalMemories * 1024 * 0.1),
            indices: Math.floor(stats.totalMemories * 1024 * 0.05)
          },
          growthTrend: stats.recentActivity.map(activity => ({
            date: activity.date,
            count: activity.count,
            size: activity.count * 1024
          }))
        },
        performance: {
          searchLatency: {
            average: 45,
            p50: 35,
            p95: 120,
            p99: 250
          },
          indexingLatency: {
            average: 150,
            p95: 400
          },
          throughput: {
            searchesPerSecond: 50 + Math.random() * 20,
            indexingPerSecond: 10 + Math.random() * 5
          },
          cacheHitRate: 0.75 + Math.random() * 0.2,
          errorRate: Math.random() * 0.05
        },
        content: {
          confidenceDistribution: [
            { range: '0.0-0.2', count: Math.floor(stats.totalMemories * 0.05) },
            { range: '0.2-0.4', count: Math.floor(stats.totalMemories * 0.1) },
            { range: '0.4-0.6', count: Math.floor(stats.totalMemories * 0.15) },
            { range: '0.6-0.8', count: Math.floor(stats.totalMemories * 0.35) },
            { range: '0.8-1.0', count: Math.floor(stats.totalMemories * 0.35) }
          ],
          tagDistribution: stats.topTags.map(tag => ({
            tag: tag.tag,
            count: tag.count,
            percentage: (tag.count / stats.totalMemories) * 100
          })),
          clusterDistribution: [
            { cluster: 'technical', count: Math.floor(stats.totalMemories * 0.3), avgConfidence: 0.82 },
            { cluster: 'personal', count: Math.floor(stats.totalMemories * 0.25), avgConfidence: 0.78 },
            { cluster: 'work', count: Math.floor(stats.totalMemories * 0.2), avgConfidence: 0.85 },
            { cluster: 'general', count: Math.floor(stats.totalMemories * 0.25), avgConfidence: 0.75 }
          ],
          contentTypes: [
            { type: 'text', count: Math.floor(stats.totalMemories * 0.7), avgSize: 512 },
            { type: 'code', count: Math.floor(stats.totalMemories * 0.15), avgSize: 1024 },
            { type: 'structured', count: Math.floor(stats.totalMemories * 0.1), avgSize: 256 },
            { type: 'other', count: Math.floor(stats.totalMemories * 0.05), avgSize: 128 }
          ],
          relationshipStats: {
            totalConnections: Math.floor(stats.totalMemories * 2.5),
            avgConnectionsPerMemory: 2.5,
            stronglyConnectedClusters: 4
          }
        },
        trends: {
          accessPatterns: stats.recentActivity.map(activity => ({
            date: activity.date,
            count: activity.count,
            uniqueUsers: Math.floor(activity.count * 0.3)
          })),
          creationPatterns: stats.recentActivity.map(activity => ({
            date: activity.date,
            count: Math.floor(activity.count * 0.8),
            avgConfidence: 0.75 + Math.random() * 0.2
          })),
          searchPatterns: stats.recentActivity.map(activity => ({
            date: activity.date,
            queries: Math.floor(activity.count * 1.5),
            avgLatency: 40 + Math.random() * 30
          })),
          retentionCurve: [
            { age: 1, retentionRate: 0.95 },
            { age: 7, retentionRate: 0.88 },
            { age: 30, retentionRate: 0.75 },
            { age: 90, retentionRate: 0.60 },
            { age: 180, retentionRate: 0.45 },
            { age: 365, retentionRate: 0.30 }
          ]
        }
      };

      setAnalytics(mockAnalytics);
      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch analytics';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, memoryService, onError]);

  // Initial load and refresh interval
  useEffect(() => {
    fetchAnalytics();
    
    if (refreshInterval > 0) {
      const interval = setInterval(fetchAnalytics, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchAnalytics, refreshInterval]);

  // Chart configurations
  const chartConfigs = useMemo(() => {
    if (!analytics) return {};

    return {
      memoryGrowth: {
        data: analytics.usage.growthTrend,
        axes: [
          { type: 'time', position: 'bottom', label: { format: '%b %d' } },
          { type: 'number', position: 'left', title: { text: 'Memory Count' } }
        ],
        series: [{
          type: 'line',
          xKey: 'date',
          yKey: 'count',
          stroke: '#2196F3',
          marker: { enabled: true }
        }],
        title: { text: 'Memory Growth Over Time' }
      } as AgChartOptions,

      confidenceDistribution: {
        data: analytics.content.confidenceDistribution,
        series: [{
          type: 'column',
          xKey: 'range',
          yKey: 'count',
          fill: '#4CAF50'
        }],
        axes: [
          { type: 'category', position: 'bottom', title: { text: 'Confidence Range' } },
          { type: 'number', position: 'left', title: { text: 'Memory Count' } }
        ],
        title: { text: 'Confidence Score Distribution' }
      } as unknown,

      clusterDistribution: {
        data: analytics.content.clusterDistribution,
        series: [{
          type: 'pie',
          angleKey: 'count',
          labelKey: 'cluster',
          label: { enabled: true }
        }],
        title: { text: 'Memory Distribution by Cluster' }
      } as unknown,

      retentionCurve: {
        data: analytics.trends.retentionCurve,
        axes: [
          { type: 'number', position: 'bottom', title: { text: 'Age (days)' } },
          { type: 'number', position: 'left', title: { text: 'Retention Rate' }, label: { format: '.0%' } }
        ],
        series: [{
          type: 'line',
          xKey: 'age',
          yKey: 'retentionRate',
          stroke: '#FF9800',
          marker: { enabled: true }
        }],
        title: { text: 'Memory Retention Curve' }
      } as AgChartOptions,

      performanceMetrics: {
        data: analytics.trends.searchPatterns,
        axes: [
          { type: 'time', position: 'bottom', label: { format: '%b %d' } },
          { type: 'number', position: 'left', title: { text: 'Queries' } },
          { type: 'number', position: 'right', title: { text: 'Latency (ms)' } }
        ],
        series: [
          {
            type: 'column',
            xKey: 'date',
            yKey: 'queries',
            fill: '#2196F3',
            yName: 'Queries'
          },
          {
            type: 'line',
            xKey: 'date',
            yKey: 'avgLatency',
            stroke: '#F44336',
            yName: 'Avg Latency',
            marker: { enabled: true }
          }
        ],
        title: { text: 'Search Performance Over Time' }
      } as AgChartOptions
    };
  }, [analytics]);

  if (error) {
    return (
      <Card className="p-6 sm:p-4 md:p-6">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <Activity className="w-12 h-12 mx-auto mb-2 " />
            <h3 className="text-lg font-semibold">Analytics Error</h3>
          </div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={fetchAnalytics} variant="outline" >
            <RefreshCw className="w-4 h-4 mr-2 " />
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6" style={{ height: `${height}px` }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Memory Analytics</h2>
          <p className="text-gray-600">
            {lastUpdated && (
              <span className="ml-2 text-sm md:text-base lg:text-lg">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <Button onClick={fetchAnalytics} disabled={loading} variant="outline" >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Memories"
          value={analytics?.usage.totalMemories || 0}
          icon={<Database className="w-6 h-6 " />}
          color="blue"
          loading={loading}
        />
        <MetricCard
          title="Storage Size"
          value={analytics ? `${(analytics.vectorStore.storageSize / 1024 / 1024).toFixed(1)} MB` : '0 MB'}
          icon={<Activity className="w-6 h-6 " />}
          color="green"
          loading={loading}
        />
        <MetricCard
          title="Avg Search Latency"
          value={analytics ? `${analytics.performance.searchLatency.average.toFixed(0)}ms` : '0ms'}
          icon={<Clock className="w-6 h-6 " />}
          color="orange"
          loading={loading}
        />
        <MetricCard
          title="Search Accuracy"
          value={analytics ? `${(analytics.vectorStore.searchAccuracy * 100).toFixed(1)}%` : '0%'}
          icon={<Zap className="w-6 h-6 " />}
          color="purple"
          loading={loading}
        />
      </div>

      {/* Detailed Analytics Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6 sm:p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-4">Memory Growth</h3>
              {loading ? (
                <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
              ) : chartConfigs.memoryGrowth ? (
                <div className="h-64">
                  <AgCharts options={chartConfigs.memoryGrowth} />
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                </div>
              )}
            </Card>

            <Card className="p-6 sm:p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-4">Cluster Distribution</h3>
              {loading ? (
                <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
              ) : chartConfigs.clusterDistribution ? (
                <div className="h-64">
                  <AgCharts options={chartConfigs.clusterDistribution} />
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                </div>
              )}
            </Card>
          </div>

          {/* Storage Breakdown */}
          <Card className="p-6 sm:p-4 md:p-6">
            <h3 className="text-lg font-semibold mb-4">Storage Breakdown</h3>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-4 bg-gray-200 animate-pulse rounded"></div>
                ))}
              </div>
            ) : analytics && (
              <div className="space-y-4">
                {Object.entries(analytics.usage.storageBreakdown).map(([type, size]) => {
                  const percentage = (size / analytics.vectorStore.storageSize) * 100;
                  return (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-blue-500 rounded "></div>
                        <span className="capitalize font-medium">{type}</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="w-32 bg-gray-200 rounded-full h-2 ">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-16 text-right ">
                          {(size / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6 sm:p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-4">Search Performance</h3>
              {loading ? (
                <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
              ) : chartConfigs.performanceMetrics ? (
                <div className="h-64">
                  <AgCharts options={chartConfigs.performanceMetrics} />
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                </div>
              )}
            </Card>

            <Card className="p-6 sm:p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="h-16 bg-gray-200 animate-pulse rounded"></div>
                  ))}
                </div>
              ) : analytics && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded sm:p-4 md:p-6">
                    <span className="font-medium">Cache Hit Rate</span>
                    <Badge variant="secondary">
                      {(analytics.performance.cacheHitRate * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded sm:p-4 md:p-6">
                    <span className="font-medium">Error Rate</span>
                    <Badge variant={analytics.performance.errorRate > 0.05 ? "destructive" : "secondary"}>
                      {(analytics.performance.errorRate * 100).toFixed(2)}%
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded sm:p-4 md:p-6">
                    <span className="font-medium">Searches/sec</span>
                    <Badge variant="secondary">
                      {analytics.performance.throughput.searchesPerSecond.toFixed(1)}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded sm:p-4 md:p-6">
                    <span className="font-medium">Indexing/sec</span>
                    <Badge variant="secondary">
                      {analytics.performance.throughput.indexingPerSecond.toFixed(1)}
                    </Badge>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="content" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6 sm:p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-4">Confidence Distribution</h3>
              {loading ? (
                <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
              ) : chartConfigs.confidenceDistribution ? (
                <div className="h-64">
                  <AgCharts options={chartConfigs.confidenceDistribution} />
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                </div>
              )}
            </Card>

            <Card className="p-6 sm:p-4 md:p-6">
              <h3 className="text-lg font-semibold mb-4">Top Tags</h3>
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="h-8 bg-gray-200 animate-pulse rounded"></div>
                  ))}
                </div>
              ) : analytics && (
                <div className="space-y-2">
                  {analytics.content.tagDistribution.slice(0, 10).map((tag, index) => (
                    <div key={tag.tag} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded sm:p-4 md:p-6">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">#{index + 1}</span>
                        <Badge variant="outline">{tag.tag}</Badge>
                      </div>
                      <div className="text-sm text-gray-600 md:text-base lg:text-lg">
                        {tag.count} ({tag.percentage.toFixed(1)}%)
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card className="p-6 sm:p-4 md:p-6">
            <h3 className="text-lg font-semibold mb-4">Memory Retention Curve</h3>
            {loading ? (
              <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
            ) : chartConfigs.retentionCurve ? (
              <div className="h-64">
                <AgCharts options={chartConfigs.retentionCurve} />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
              </div>
            )}
          </Card>

          {/* Memory Decay Patterns */}
          <Card className="p-6 sm:p-4 md:p-6">
            <h3 className="text-lg font-semibold mb-4">Memory Decay Patterns</h3>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-16 bg-gray-200 animate-pulse rounded"></div>
                ))}
              </div>
            ) : analytics && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {analytics.vectorStore.memoryDecay.map((decay, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                    <div className="text-sm font-medium text-gray-600 mb-2 md:text-base lg:text-lg">
                      {decay.timeRange}
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Retention</span>
                        <span className="font-medium">
                          {(decay.retentionRate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Access Freq</span>
                        <span className="font-medium">
                          {(decay.accessFrequency * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Forgetting</span>
                        <span className="font-medium">
                          {(decay.forgettingCurve * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MemoryAnalytics;
