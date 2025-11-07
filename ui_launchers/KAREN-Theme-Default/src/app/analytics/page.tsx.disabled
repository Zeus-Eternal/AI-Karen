'use client';

import React from 'react';
import { ModernSidebar } from '@/components/layout/ModernSidebar';
import { ModernHeader } from '@/components/layout/ModernHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MetricCard } from '@/components/ui/metric-card';
import { Sparkline } from '@/components/ui/sparkline';
import {
  BarChart3,
  TrendingUp,
  Users,
  MessageSquare,
  DollarSign,
  Clock,
} from 'lucide-react';
import { AnimatedNumber } from '@/components/ui/animated-number';

export default function AnalyticsLabPage() {
  const sparklineData = [45, 52, 49, 60, 58, 65, 70, 68, 75, 80, 78, 85, 90, 88, 95, 100];

  return (
    <div className="min-h-screen bg-background">
      <ModernSidebar />
      <ModernHeader />

      <main className="ml-64 mt-16 p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-emerald-600">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Analytics Lab</h1>
                <p className="text-muted-foreground">
                  Deep insights into usage, performance, and system behavior
                </p>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Total Users"
              value={<AnimatedNumber value={1247} />}
              subtitle="Active users"
              icon={Users}
              variant="primary"
              trend={{ value: 12.5, isPositive: true }}
            />
            <MetricCard
              title="Conversations"
              value={<AnimatedNumber value={34567} />}
              subtitle="This month"
              icon={MessageSquare}
              variant="success"
              trend={{ value: 8.3, isPositive: true }}
            />
            <MetricCard
              title="API Costs"
              value={`$${1234}`}
              subtitle="This month"
              icon={DollarSign}
              variant="warning"
              trend={{ value: 5.2, isPositive: false }}
            />
            <MetricCard
              title="Avg Response Time"
              value="234ms"
              subtitle="p95 latency"
              icon={Clock}
              variant="default"
            />
          </div>

          {/* Analytics Tabs */}
          <Card>
            <CardContent className="p-6">
              <Tabs defaultValue="usage" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
                  <TabsTrigger value="models">Model Performance</TabsTrigger>
                  <TabsTrigger value="cost">Cost Analysis</TabsTrigger>
                  <TabsTrigger value="quality">Quality Metrics</TabsTrigger>
                </TabsList>

                <TabsContent value="usage" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Daily Active Users</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold mb-4">
                          <AnimatedNumber value={423} />
                        </div>
                        <Sparkline
                          data={sparklineData}
                          width={400}
                          height={80}
                          strokeColor="rgb(59, 130, 246)"
                          fillColor="rgb(59, 130, 246)"
                          showArea
                        />
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Message Volume</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold mb-4">
                          <AnimatedNumber value={12543} />
                        </div>
                        <Sparkline
                          data={sparklineData.map(v => v * 1.5)}
                          width={400}
                          height={80}
                          strokeColor="rgb(34, 197, 94)"
                          fillColor="rgb(34, 197, 94)"
                          showArea
                        />
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="models" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Model Usage Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">GPT-4</span>
                            <span className="text-sm text-muted-foreground">45%</span>
                          </div>
                          <div className="h-2 bg-secondary rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500" style={{ width: '45%' }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Claude 3.5 Sonnet</span>
                            <span className="text-sm text-muted-foreground">30%</span>
                          </div>
                          <div className="h-2 bg-secondary rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500" style={{ width: '30%' }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">GPT-3.5</span>
                            <span className="text-sm text-muted-foreground">15%</span>
                          </div>
                          <div className="h-2 bg-secondary rounded-full overflow-hidden">
                            <div className="h-full bg-green-500" style={{ width: '15%' }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Llama 3</span>
                            <span className="text-sm text-muted-foreground">10%</span>
                          </div>
                          <div className="h-2 bg-secondary rounded-full overflow-hidden">
                            <div className="h-full bg-orange-500" style={{ width: '10%' }} />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="cost" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Daily Costs</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-3xl font-bold mb-4">
                          $<AnimatedNumber value={47} />
                        </div>
                        <Sparkline
                          data={[30, 35, 40, 38, 42, 45, 47, 50, 48, 46, 44, 47]}
                          width={400}
                          height={80}
                          strokeColor="rgb(245, 158, 11)"
                          fillColor="rgb(245, 158, 11)"
                          showArea
                        />
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Cost per Model</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">GPT-4</span>
                          <span className="text-sm font-semibold">$892</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Claude 3.5</span>
                          <span className="text-sm font-semibold">$234</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">GPT-3.5</span>
                          <span className="text-sm font-semibold">$78</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Llama 3 (Local)</span>
                          <span className="text-sm font-semibold">$0</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="quality" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Success Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-4xl font-bold text-green-600">
                          <AnimatedNumber value={98.7} />%
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          Successful completions
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">User Satisfaction</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-4xl font-bold text-blue-600">
                          <AnimatedNumber value={4.7} formatFn={(v) => v.toFixed(1)} />
                          <span className="text-2xl">/5</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          Average rating
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Error Rate</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-4xl font-bold text-yellow-600">
                          <AnimatedNumber value={1.3} formatFn={(v) => v.toFixed(1)} />%
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          Failed requests
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
