'use client';

import React from 'react';
import { ModernSidebar } from '@/components/layout/ModernSidebar';
import { ModernHeader } from '@/components/layout/ModernHeader';
import { MetricCard } from '@/components/ui/metric-card';
import { CommandCenter } from '@/components/ai-command-center/CommandCenter';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkline } from '@/components/ui/sparkline';
import { AnimatedNumber } from '@/components/ui/animated-number';
import {
  Activity,
  Cpu,
  Database,
  Zap,
  Users,
  MessageSquare,
  TrendingUp,
  Clock,
} from 'lucide-react';

export default function DashboardPage() {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);

  // Mock data
  const metricsData = {
    modelRequests: 12543,
    activeAgents: 4,
    memoryVectors: 89234,
    pluginsActive: 12,
    responseTime: 234,
    tokenUsage: 1234567,
  };

  const sparklineData = [
    45, 52, 49, 60, 58, 65, 70, 68, 75, 80, 78, 85, 90, 88, 95, 100,
  ];

  return (
    <div className="min-h-screen bg-background">
      <ModernSidebar />
      <ModernHeader sidebarCollapsed={sidebarCollapsed} />

      {/* Main Content */}
      <main className="ml-64 mt-16 p-6 transition-all duration-300">
        <div className="space-y-6">
          {/* Page Header */}
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor and control your AI operations from a single command center
            </p>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Model Requests"
              value={<AnimatedNumber value={metricsData.modelRequests} />}
              subtitle="Last 24 hours"
              icon={MessageSquare}
              variant="primary"
              trend={{
                value: 12.5,
                isPositive: true,
              }}
            />
            <MetricCard
              title="Active Agents"
              value={<AnimatedNumber value={metricsData.activeAgents} />}
              subtitle="Currently running"
              icon={Zap}
              variant="success"
            />
            <MetricCard
              title="Memory Vectors"
              value={<AnimatedNumber value={metricsData.memoryVectors} />}
              subtitle="Stored embeddings"
              icon={Database}
              variant="default"
              trend={{
                value: 8.3,
                isPositive: true,
              }}
            />
            <MetricCard
              title="Active Plugins"
              value={<AnimatedNumber value={metricsData.pluginsActive} />}
              subtitle="Enabled extensions"
              icon={Activity}
              variant="default"
            />
          </div>

          {/* Performance Overview */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Response Time
                </CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  <AnimatedNumber value={metricsData.responseTime} />ms
                </div>
                <div className="mt-4">
                  <Sparkline
                    data={sparklineData}
                    width={200}
                    height={40}
                    strokeColor="rgb(59, 130, 246)"
                    fillColor="rgb(59, 130, 246)"
                    showArea
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Token Usage
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  <AnimatedNumber value={metricsData.tokenUsage} />
                </div>
                <div className="mt-4">
                  <Sparkline
                    data={sparklineData.map((v) => v * 1.2)}
                    width={200}
                    height={40}
                    strokeColor="rgb(168, 85, 247)"
                    fillColor="rgb(168, 85, 247)"
                    showArea
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  CPU Usage
                </CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  <AnimatedNumber value={45} />%
                </div>
                <div className="mt-4">
                  <Sparkline
                    data={sparklineData.map((v) => v * 0.6)}
                    width={200}
                    height={40}
                    strokeColor="rgb(34, 197, 94)"
                    fillColor="rgb(34, 197, 94)"
                    showArea
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* AI Command Center */}
          <CommandCenter />
        </div>
      </main>
    </div>
  );
}
