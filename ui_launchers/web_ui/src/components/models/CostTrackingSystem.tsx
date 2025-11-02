/**
 * Cost Tracking System
 * Budget alerts and usage optimization recommendations
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  Bell,
  Settings,
  Target,
  Lightbulb,
  Calendar,
  BarChart3,
  PieChart,
  Plus,
  Edit,
  Trash2,
  Save
} from 'lucide-react';
import { BudgetAlert } from '@/types/providers';
import { useToast } from '@/hooks/use-toast';
interface CostTrackingSystemProps {
  className?: string;
}
interface BudgetConfig {
  id: string;
  name: string;
  amount: number;
  period: 'daily' | 'weekly' | 'monthly' | 'yearly';
  providers: string[];
  models: string[];
  alertThresholds: number[];
  enabled: boolean;
  createdAt: Date;
}
interface CostBreakdown {
  provider: string;
  model: string;
  requests: number;
  cost: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
}
interface OptimizationSuggestion {
  id: string;
  type: 'model_switch' | 'usage_reduction' | 'batch_optimization' | 'provider_switch';
  title: string;
  description: string;
  potentialSavings: number;
  confidence: number;
  implementation: string[];
  impact: 'low' | 'medium' | 'high';
}
interface CostData {
  totalSpend: number;
  budgetUtilization: number;
  projectedSpend: number;
  breakdown: CostBreakdown[];
  trends: {
    daily: { date: Date; cost: number }[];
    weekly: { week: string; cost: number }[];
    monthly: { month: string; cost: number }[];
  };
  topSpenders: {
    provider: string;
    cost: number;
    percentage: number;
  }[];
}
const CostTrackingSystem: React.FC<CostTrackingSystemProps> = ({ className }) => {
  const { toast } = useToast();
  const [costData, setCostData] = useState<CostData | null>(null);
  const [budgets, setBudgets] = useState<BudgetConfig[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [editingBudget, setEditingBudget] = useState<BudgetConfig | null>(null);
  const [showBudgetDialog, setShowBudgetDialog] = useState(false);
  useEffect(() => {
    loadCostData();
    loadBudgets();
    loadAlerts();
    loadOptimizationSuggestions();
  }, [selectedPeriod]);
  const loadCostData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/costs/data?period=${selectedPeriod}`);
      if (!response.ok) throw new Error('Failed to load cost data');
      const data = await response.json();
      setCostData(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load cost data',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };
  const loadBudgets = async () => {
    try {
      const response = await fetch('/api/costs/budgets');
      if (!response.ok) throw new Error('Failed to load budgets');
      const data = await response.json();
      setBudgets(data.budgets || []);
    } catch (error) {
    }
  };
  const loadAlerts = async () => {
    try {
      const response = await fetch('/api/costs/alerts');
      if (!response.ok) throw new Error('Failed to load alerts');
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
    }
  };
  const loadOptimizationSuggestions = async () => {
    try {
      const response = await fetch('/api/costs/optimization-suggestions');
      if (!response.ok) throw new Error('Failed to load suggestions');
      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (error) {
    }
  };
  const saveBudget = async (budget: Omit<BudgetConfig, 'id' | 'createdAt'>) => {
    try {
      const response = await fetch('/api/costs/budgets', {
        method: editingBudget ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...budget,
          ...(editingBudget && { id: editingBudget.id })
        })
      });
      if (!response.ok) throw new Error('Failed to save budget');
      const savedBudget = await response.json();
      if (editingBudget) {
        setBudgets(prev => prev.map(b => b.id === editingBudget.id ? savedBudget : b));
      } else {
        setBudgets(prev => [...prev, savedBudget]);
      }
      setShowBudgetDialog(false);
      setEditingBudget(null);
      toast({
        title: 'Budget Saved',
        description: `Budget "${budget.name}" has been saved successfully`
      });
    } catch (error) {
      toast({
        title: 'Save Error',
        description: 'Failed to save budget configuration',
        variant: 'destructive'
      });
    }
  };
  const deleteBudget = async (budgetId: string) => {
    if (!confirm('Are you sure you want to delete this budget?')) return;
    try {
      const response = await fetch(`/api/costs/budgets/${budgetId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete budget');
      setBudgets(prev => prev.filter(b => b.id !== budgetId));
      toast({
        title: 'Budget Deleted',
        description: 'Budget has been deleted successfully'
      });
    } catch (error) {
      toast({
        title: 'Delete Error',
        description: 'Failed to delete budget',
        variant: 'destructive'
      });
    }
  };
  const dismissAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/costs/alerts/${alertId}/dismiss`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to dismiss alert');
      setAlerts(prev => prev.filter(a => a.id !== alertId));
      toast({
        title: 'Alert Dismissed',
        description: 'Alert has been dismissed'
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to dismiss alert',
        variant: 'destructive'
      });
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
  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-red-600 sm:w-auto md:w-full" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-green-600 sm:w-auto md:w-full" />;
      default:
        return <BarChart3 className="w-4 h-4 text-gray-600 sm:w-auto md:w-full" />;
    }
  };
  const getAlertSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50';
      default:
        return 'border-blue-500 bg-blue-50';
    }
  };
  const BudgetDialog: React.FC<{ budget?: BudgetConfig; onSave: (budget: any) => void }> = ({ 
    budget, 
    onSave 
  }) => {
    const [formData, setFormData] = useState({
      name: budget?.name || '',
      amount: budget?.amount || 0,
      period: budget?.period || 'monthly',
      providers: budget?.providers || [],
      models: budget?.models || [],
      alertThresholds: budget?.alertThresholds || [80, 90, 100],
      enabled: budget?.enabled !== false
    });
    const handleSave = () => {
      if (!formData.name || formData.amount <= 0) {
        toast({
          title: 'Validation Error',
          description: 'Please provide a name and valid amount',
          variant: 'destructive'
        });
        return;
      }
      onSave(formData);
    };
    return (
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{budget ? 'Edit Budget' : 'Create Budget'}</DialogTitle>
          <DialogDescription>
            Set up budget limits and alert thresholds for cost monitoring
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Budget Name</Label>
            <input
              id="name"
              value={formData.name}
              onChange={(e) = aria-label="Input"> setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Monthly AI Budget"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="amount">Amount</Label>
              <input
                id="amount"
                type="number"
                value={formData.amount}
                onChange={(e) = aria-label="Input"> setFormData(prev => ({ ...prev, amount: Number(e.target.value) }))}
                placeholder="0.00"
              />
            </div>
            <div>
              <Label htmlFor="period">Period</Label>
              <select value={formData.period} onValueChange={(value: any) = aria-label="Select option"> setFormData(prev => ({ ...prev, period: value }))}>
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="daily" aria-label="Select option">Daily</SelectItem>
                  <selectItem value="weekly" aria-label="Select option">Weekly</SelectItem>
                  <selectItem value="monthly" aria-label="Select option">Monthly</SelectItem>
                  <selectItem value="yearly" aria-label="Select option">Yearly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label>Alert Thresholds (%)</Label>
            <div className="grid grid-cols-3 gap-2 mt-1">
              {formData.alertThresholds.map((threshold, idx) => (
                <input
                  key={idx}
                  type="number"
                  value={threshold}
                  onChange={(e) = aria-label="Input"> {
                    const newThresholds = [...formData.alertThresholds];
                    newThresholds[idx] = Number(e.target.value);
                    setFormData(prev => ({ ...prev, alertThresholds: newThresholds }));
                  }}
                  placeholder={`${(idx + 1) * 30}%`}
                />
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button variant="outline" onClick={() = aria-label="Button"> setShowBudgetDialog(false)}>
              Cancel
            </Button>
            <button onClick={handleSave} aria-label="Button">
              <Save className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
              Save Budget
            </Button>
          </div>
        </div>
      </DialogContent>
    );
  };
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-8 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <DollarSign className="w-8 h-8 animate-pulse mx-auto text-green-500 sm:w-auto md:w-full" />
            <div>Loading cost data...</div>
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
                <DollarSign className="w-5 h-5 sm:w-auto md:w-full" />
                Cost Tracking & Budget Management
              </CardTitle>
              <CardDescription>
                Monitor spending, set budgets, and optimize costs across all AI providers
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <select value={selectedPeriod} onValueChange={(value: any) = aria-label="Select option"> setSelectedPeriod(value)}>
                <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="daily" aria-label="Select option">Daily</SelectItem>
                  <selectItem value="weekly" aria-label="Select option">Weekly</SelectItem>
                  <selectItem value="monthly" aria-label="Select option">Monthly</SelectItem>
                </SelectContent>
              </Select>
              <Dialog open={showBudgetDialog} onOpenChange={setShowBudgetDialog}>
                <DialogTrigger asChild>
                  <button aria-label="Button">
                    <Plus className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                    Add Budget
                  </Button>
                </DialogTrigger>
                <BudgetDialog onSave={saveBudget} />
              </Dialog>
            </div>
          </div>
        </CardHeader>
      </Card>
      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Bell className="w-5 h-5 sm:w-auto md:w-full" />
            Budget Alerts ({alerts.length})
          </h3>
          {alerts.map(alert => (
            <Alert key={alert.id} className={getAlertSeverityColor(alert.severity)}>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 mt-0.5 sm:w-auto md:w-full" />
                  <div>
                    <div className="font-medium">{alert.title}</div>
                    <AlertDescription className="mt-1">
                      {alert.message}
                    </AlertDescription>
                    <div className="mt-2 flex items-center gap-4 text-sm md:text-base lg:text-lg">
                      <span>Current: {formatCurrency(alert.currentSpend)}</span>
                      <span>Threshold: {formatCurrency(alert.threshold)}</span>
                      <span>Timeframe: {alert.timeframe}</span>
                    </div>
                    {alert.recommendations.length > 0 && (
                      <div className="mt-2">
                        <div className="text-sm font-medium md:text-base lg:text-lg">Recommendations:</div>
                        <ul className="text-sm text-gray-600 list-disc list-inside md:text-base lg:text-lg">
                          {alert.recommendations.slice(0, 2).map((rec, idx) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                    {alert.severity}
                  </Badge>
                  <button
                    size="sm"
                    variant="ghost"
                    onClick={() = aria-label="Button"> dismissAlert(alert.id)}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </Alert>
          ))}
        </div>
      )}
      {/* Cost Overview */}
      {costData && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Total Spend</p>
                  <p className="text-2xl font-bold">{formatCurrency(costData.totalSpend)}</p>
                </div>
                <DollarSign className="w-8 h-8 text-green-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Budget Used</p>
                  <p className="text-2xl font-bold">{(costData.budgetUtilization * 100).toFixed(1)}%</p>
                </div>
                <Target className="w-8 h-8 text-blue-500 sm:w-auto md:w-full" />
              </div>
              <Progress value={costData.budgetUtilization * 100} className="mt-2 h-2" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Projected</p>
                  <p className="text-2xl font-bold">{formatCurrency(costData.projectedSpend)}</p>
                </div>
                <TrendingUp className="w-8 h-8 text-orange-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 sm:p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 md:text-base lg:text-lg">Top Provider</p>
                  <p className="text-lg font-bold">{costData.topSpenders[0]?.provider || 'N/A'}</p>
                  <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                    {costData.topSpenders[0] ? formatCurrency(costData.topSpenders[0].cost) : ''}
                  </p>
                </div>
                <PieChart className="w-8 h-8 text-purple-500 sm:w-auto md:w-full" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Budget Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 sm:w-auto md:w-full" />
              Budget Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {budgets.map(budget => (
                <div key={budget.id} className="p-4 border rounded-lg sm:p-4 md:p-6">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium">{budget.name}</h4>
                      <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                        {formatCurrency(budget.amount)} / {budget.period}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={budget.enabled ? 'default' : 'secondary'}>
                        {budget.enabled ? 'Active' : 'Inactive'}
                      </Badge>
                      <button
                        size="sm"
                        variant="ghost"
                        onClick={() = aria-label="Button"> {
                          setEditingBudget(budget);
                          setShowBudgetDialog(true);
                        }}
                      >
                        <Edit className="w-3 h-3 sm:w-auto md:w-full" />
                      </Button>
                      <button
                        size="sm"
                        variant="ghost"
                        onClick={() = aria-label="Button"> deleteBudget(budget.id)}
                      >
                        <Trash2 className="w-3 h-3 sm:w-auto md:w-full" />
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm md:text-base lg:text-lg">
                      <span>Alert Thresholds</span>
                      <span>{budget.alertThresholds.join('%, ')}%</span>
                    </div>
                    {budget.providers.length > 0 && (
                      <div className="flex justify-between text-sm md:text-base lg:text-lg">
                        <span>Providers</span>
                        <span>{budget.providers.length} selected</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {budgets.length === 0 && (
                <div className="text-center py-6 text-gray-500">
                  <Target className="w-8 h-8 mx-auto mb-2 opacity-50 sm:w-auto md:w-full" />
                  <div>No budgets configured</div>
                  <div className="text-xs sm:text-sm md:text-base">Create a budget to start monitoring costs</div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
        {/* Cost Breakdown */}
        {costData && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5 sm:w-auto md:w-full" />
                Cost Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {costData.breakdown.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {getTrendIcon(item.trend)}
                        <span className="font-medium">{item.provider}</span>
                      </div>
                      <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                        {item.model}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{formatCurrency(item.cost)}</div>
                      <div className="text-xs text-gray-600 sm:text-sm md:text-base">
                        {item.requests} requests ({item.percentage.toFixed(1)}%)
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      {/* Optimization Suggestions */}
      {suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 sm:w-auto md:w-full" />
              Cost Optimization Suggestions
            </CardTitle>
            <CardDescription>
              AI-generated recommendations to reduce costs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {suggestions.slice(0, 4).map(suggestion => (
                <div key={suggestion.id} className="p-4 border rounded-lg sm:p-4 md:p-6">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-medium">{suggestion.title}</h4>
                      <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">{suggestion.description}</p>
                    </div>
                    <Badge variant={suggestion.impact === 'high' ? 'default' : 'secondary'}>
                      {suggestion.impact} impact
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between mt-3">
                    <div className="text-sm md:text-base lg:text-lg">
                      <span className="font-medium text-green-600">
                        Save {formatCurrency(suggestion.potentialSavings)}
                      </span>
                      <span className="text-gray-600 ml-2">
                        ({suggestion.confidence}% confidence)
                      </span>
                    </div>
                    <button size="sm" variant="outline" aria-label="Button">
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      {/* Edit Budget Dialog */}
      {editingBudget && (
        <Dialog open={showBudgetDialog} onOpenChange={setShowBudgetDialog}>
          <BudgetDialog budget={editingBudget} onSave={saveBudget} />
        </Dialog>
      )}
    </div>
  );
};
export default CostTrackingSystem;
