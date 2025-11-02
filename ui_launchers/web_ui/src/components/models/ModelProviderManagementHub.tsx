/**
 * Model and Provider Management Hub
 * Main orchestrator component integrating all model and provider management functionality
 * Implements Task 5: Model and Provider Management Enhancement
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Settings, 
  Zap, 
  BarChart3, 
  Shield, 
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Activity,
  TrendingUp,
  DollarSign,
  Target,
  Brain,
  Server,
  Cloud
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
// Import all the implemented components
import EnhancedModelSelector from './EnhancedModelSelector';
import ModelMetricsDashboard from './ModelMetricsDashboard';
import CostTrackingSystem from './CostTrackingSystem';
import { ProviderConfigInterface, FallbackConfigInterface } from '../providers';
import ModelComparisonInterface from './ModelComparisonInterface';
import IntelligentModelSelector from './IntelligentModelSelector';
interface ModelProviderManagementHubProps {
  className?: string;
}
interface SystemStatus {
  models: {
    total: number;
    active: number;
    healthy: number;
    issues: number;
  };
  providers: {
    total: number;
    connected: number;
    healthy: number;
    issues: number;
  };
  performance: {
    averageLatency: number;
    successRate: number;
    requestsPerMinute: number;
    errorRate: number;
  };
  costs: {
    totalSpend: number;
    budgetUtilization: number;
    projectedSpend: number;
    topProvider: string;
  };
  fallback: {
    totalFailovers: number;
    successRate: number;
    averageRecoveryTime: number;
    activeChains: number;
  };
}
interface RecentActivity {
  id: string;
  type: 'model_selected' | 'provider_added' | 'fallback_triggered' | 'cost_alert' | 'performance_issue';
  title: string;
  description: string;
  timestamp: Date;
  severity: 'info' | 'warning' | 'error';
  metadata?: Record<string, any>;
}
const ModelProviderManagementHub: React.FC<ModelProviderManagementHubProps> = ({ className }) => {
  const { toast } = useToast();
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  useEffect(() => {
    loadSystemStatus();
    loadRecentActivity();
    // Set up real-time updates
    const interval = setInterval(() => {
      loadSystemStatus();
      loadRecentActivity();
    }, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);
  const loadSystemStatus = async () => {
    try {
      const response = await fetch('/api/models/system-status');
      if (!response.ok) throw new Error('Failed to load system status');
      const data = await response.json();
      setSystemStatus(data.status);
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };
  const loadRecentActivity = async () => {
    try {
      const response = await fetch('/api/models/recent-activity?limit=10');
      if (!response.ok) throw new Error('Failed to load recent activity');
      const data = await response.json();
      setRecentActivity(data.activities || []);
    } catch (error) {
    }
  };
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        loadSystemStatus(),
        loadRecentActivity()
      ]);
      toast({
        title: 'System Refreshed',
        description: 'All data has been updated successfully'
      });
    } catch (error) {
      toast({
        title: 'Refresh Error',
        description: 'Failed to refresh system data',
        variant: 'destructive'
      });
    } finally {
      setRefreshing(false);
    }
  };
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'model_selected':
        return <Brain className="w-4 h-4 text-blue-600 sm:w-auto md:w-full" />;
      case 'provider_added':
        return <Server className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />;
      case 'fallback_triggered':
        return <Shield className="w-4 h-4 text-yellow-600 sm:w-auto md:w-full" />;
      case 'cost_alert':
        return <DollarSign className="w-4 h-4 text-red-600 sm:w-auto md:w-full" />;
      case 'performance_issue':
        return <AlertTriangle className="w-4 h-4 text-orange-600 sm:w-auto md:w-full" />;
      default:
        return <Activity className="w-4 h-4 text-gray-600 sm:w-auto md:w-full" />;
    }
  };
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'text-red-600';
      case 'warning':
        return 'text-yellow-600';
      default:
        return 'text-blue-600';
    }
  };
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <Settings className="w-8 h-8 animate-spin mx-auto text-blue-500 sm:w-auto md:w-full" />
            <div>Loading model and provider management...</div>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-6 h-6 sm:w-auto md:w-full" />
                Model & Provider Management Hub
              </CardTitle>
              <CardDescription>
                Comprehensive management of AI models, providers, and system performance
              </CardDescription>
            </div>
            <button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={refreshing}
             aria-label="Button">
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </CardHeader>
      </Card>
      {/* System Status Overview */}
      {systemStatus && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Active Models</p>
                  <p className="text-2xl font-bold">{systemStatus.models.active}</p>
                  <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                    {systemStatus.models.healthy} healthy, {systemStatus.models.issues} issues
                  </p>
                </div>
                <Brain className="w-8 h-8 text-blue-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Providers</p>
                  <p className="text-2xl font-bold">{systemStatus.providers.connected}</p>
                  <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                    {systemStatus.providers.healthy} healthy, {systemStatus.providers.issues} issues
                  </p>
                </div>
                <Server className="w-8 h-8 text-green-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Success Rate</p>
                  <p className="text-2xl font-bold">{(systemStatus.performance.successRate * 100).toFixed(1)}%</p>
                  <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                    {systemStatus.performance.averageLatency.toFixed(0)}ms avg latency
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-orange-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Spend</p>
                  <p className="text-2xl font-bold">{formatCurrency(systemStatus.costs.totalSpend)}</p>
                  <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                    {(systemStatus.costs.budgetUtilization * 100).toFixed(1)}% of budget
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-purple-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Failovers</p>
                  <p className="text-2xl font-bold">{systemStatus.fallback.totalFailovers}</p>
                  <p className="text-xs text-gray-500 sm:text-sm md:text-base">
                    {(systemStatus.fallback.successRate * 100).toFixed(1)}% success rate
                  </p>
                </div>
                <Shield className="w-8 h-8 text-red-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="fallback">Fallback</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Model Selection */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 sm:w-auto md:w-full" />
                  Intelligent Model Selection
                </CardTitle>
                <CardDescription>
                  AI-powered model recommendations based on task requirements
                </CardDescription>
              </CardHeader>
              <CardContent>
                <IntelligentModelSelector
                  showRecommendations={true}
                  showPerformanceMetrics={true}
                  showCostAnalysis={true}
                />
              </CardContent>
            </Card>
            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 sm:w-auto md:w-full" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recentActivity.slice(0, 5).map(activity => (
                    <div key={activity.id} className="flex items-start gap-3">
                      {getActivityIcon(activity.type)}
                      <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                        <div className="text-sm font-medium md:text-base lg:text-lg">{activity.title}</div>
                        <div className="text-xs text-gray-600 truncate sm:text-sm md:text-base">
                          {activity.description}
                        </div>
                        <div className="text-xs text-gray-500 mt-1 sm:text-sm md:text-base">
                          {new Date(activity.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      <Badge 
                        variant={activity.severity === 'error' ? 'destructive' : 'secondary'}
                        className="text-xs sm:text-sm md:text-base"
                      >
                        {activity.severity}
                      </Badge>
                    </div>
                  ))}
                  {recentActivity.length === 0 && (
                    <div className="text-center py-4 text-gray-500">
                      <Activity className="w-6 h-6 mx-auto mb-2 opacity-50 sm:w-auto md:w-full" />
                      <div className="text-sm md:text-base lg:text-lg">No recent activity</div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
          {/* Model Comparison */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 sm:w-auto md:w-full" />
                Model Performance Comparison
              </CardTitle>
              <CardDescription>
                Compare models side-by-side across performance, cost, and capability metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ModelComparisonInterface />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5 sm:w-auto md:w-full" />
                Enhanced Model Management
              </CardTitle>
              <CardDescription>
                Comprehensive model selection with intelligent recommendations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <EnhancedModelSelector
                showStats={true}
                showActions={true}
                showScanning={true}
                showFilters={true}
                showHealthIndicators={true}
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="providers" className="space-y-6">
          <ProviderConfigInterface />
        </TabsContent>
        <TabsContent value="metrics" className="space-y-6">
          <ModelMetricsDashboard />
        </TabsContent>
        <TabsContent value="costs" className="space-y-6">
          <CostTrackingSystem />
        </TabsContent>
        <TabsContent value="fallback" className="space-y-6">
          <FallbackConfigInterface />
        </TabsContent>
      </Tabs>
    </div>
  );
};
export default ModelProviderManagementHub;
