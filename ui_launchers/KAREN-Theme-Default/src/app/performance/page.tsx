'use client';

import React from 'react';
import { ModernSidebar } from '@/components/layout/ModernSidebar';
import { ModernHeader } from '@/components/layout/ModernHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MetricCard } from '@/components/ui/metric-card';
import { Sparkline } from '@/components/ui/sparkline';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  Cpu,
  HardDrive,
  Zap,
  Clock,
  Database,
  Network,
  AlertCircle,
} from 'lucide-react';

export default function PerformancePage() {
  const sparklineData = [45, 52, 49, 60, 58, 55, 50, 48, 45, 50, 52, 49];

  return (
    <div className="min-h-screen bg-background">
      <ModernSidebar />
      <ModernHeader />

      <main className="ml-64 mt-16 p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-red-600">
                <Activity className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Performance Monitor</h1>
                <p className="text-muted-foreground">
                  Real-time system performance and resource utilization
                </p>
              </div>
            </div>
          </div>

          {/* System Health Overview */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="CPU Usage"
              value={45}
              subtitle="Percentage"
              icon={Cpu}
              variant="success"
            />
            <MetricCard
              title="Memory Usage"
              value="2.4GB"
              subtitle="of 8GB"
              icon={HardDrive}
              variant="warning"
            />
            <MetricCard
              title="Network I/O"
              value="12.4MB/s"
              subtitle="Current throughput"
              icon={Network}
              variant="primary"
            />
            <MetricCard
              title="Active Connections"
              value={234}
              subtitle="Current connections"
              icon={Zap}
              variant="default"
            />
          </div>

          {/* Resource Monitoring */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">CPU Utilization</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Overall</span>
                    <span className="text-sm font-semibold">45%</span>
                  </div>
                  <Progress value={45} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Core 1</span>
                    <span className="text-sm font-semibold">52%</span>
                  </div>
                  <Progress value={52} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Core 2</span>
                    <span className="text-sm font-semibold">38%</span>
                  </div>
                  <Progress value={38} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Core 3</span>
                    <span className="text-sm font-semibold">41%</span>
                  </div>
                  <Progress value={41} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Memory Utilization</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Total Used</span>
                    <span className="text-sm font-semibold">2.4GB / 8GB</span>
                  </div>
                  <Progress value={30} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Application</span>
                    <span className="text-sm font-semibold">1.2GB</span>
                  </div>
                  <Progress value={15} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Cache</span>
                    <span className="text-sm font-semibold">0.8GB</span>
                  </div>
                  <Progress value={10} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">System</span>
                    <span className="text-sm font-semibold">0.4GB</span>
                  </div>
                  <Progress value={5} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* API Performance */}
          <Card>
            <CardHeader>
              <CardTitle>API Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <Card className="border-2">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Clock className="h-5 w-5 text-blue-600" />
                        <span className="text-sm font-medium">Response Time</span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">p50</span>
                          <span className="font-semibold">89ms</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">p95</span>
                          <span className="font-semibold">234ms</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">p99</span>
                          <span className="font-semibold">567ms</span>
                        </div>
                      </div>
                      <Sparkline
                        data={sparklineData}
                        width={200}
                        height={40}
                        strokeColor="rgb(59, 130, 246)"
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-2">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Database className="h-5 w-5 text-green-600" />
                        <span className="text-sm font-medium">Database Queries</span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Avg Time</span>
                          <span className="font-semibold">23ms</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Queries/sec</span>
                          <span className="font-semibold">145</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Cache Hit</span>
                          <span className="font-semibold">87%</span>
                        </div>
                      </div>
                      <Sparkline
                        data={sparklineData.map(v => v * 0.5)}
                        width={200}
                        height={40}
                        strokeColor="rgb(34, 197, 94)"
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-2">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        <span className="text-sm font-medium">Error Rate</span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Total</span>
                          <span className="font-semibold">1.3%</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">4xx Errors</span>
                          <span className="font-semibold">0.8%</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">5xx Errors</span>
                          <span className="font-semibold">0.5%</span>
                        </div>
                      </div>
                      <Sparkline
                        data={[2, 1, 3, 2, 1, 2, 1, 1, 2, 1, 1, 2]}
                        width={200}
                        height={40}
                        strokeColor="rgb(245, 158, 11)"
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>

          {/* Performance Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Optimization Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-500/10">
                  <Activity className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="font-medium">Enable Query Caching</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Database query caching could reduce response time by 40ms
                    </p>
                  </div>
                  <Badge>Recommended</Badge>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-lg bg-green-500/10">
                  <Zap className="h-5 w-5 text-green-600 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="font-medium">Implement Request Batching</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Batch similar requests to reduce API calls by 25%
                    </p>
                  </div>
                  <Badge>High Impact</Badge>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/10">
                  <Database className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="font-medium">Optimize Memory Usage</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Clear old cache entries to free up 400MB of memory
                    </p>
                  </div>
                  <Badge variant="outline">Low Priority</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
